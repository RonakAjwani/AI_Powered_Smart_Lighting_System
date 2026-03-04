"""
Triage Agent — Tier 1 SOC: LLM-based alert classification and routing.

Receives context summaries from the Log Ingestion Agent and classifies them:
  - Route to DDoS Detection Agent (network-layer attacks)
  - Route to Malware Detection Agent (device/host-layer attacks)
  - Route to both (multi-vector attacks)
  - Mark as benign (no suspicious activity)

Uses an LLM to make nuanced classification decisions that rule-based systems miss,
such as distinguishing legitimate traffic spikes from DDoS indicators.

Integrates with model_registry.py for multi-provider LLM support.
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from pydantic import BaseModel
from langgraph.graph import StateGraph, END

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("triage-agent")


# ═══════════════════════════════════════════════════════════════════════════════
# Triage Classification Categories
# ═══════════════════════════════════════════════════════════════════════════════

class ThreatCategory:
    """Enumeration of threat categories for routing decisions."""
    BENIGN = "benign"
    DDOS = "ddos"
    MALWARE = "malware"
    MULTI_VECTOR = "multi_vector"
    UNKNOWN = "unknown"


# Rule-based pre-classification keywords per category
DDOS_INDICATORS = {
    "keywords": [
        "http_flood", "syn_flood", "udp_flood", "slowloris",
        "dns_amplification", "ddos", "volumetric", "rps_spike",
        "half_open_connections", "connection_exhaustion",
        "amplification", "distributed_sources",
    ],
    "mitre_ttps": ["T0813", "T0804"],  # Denial of Control, Unauthorized Command
    "network_signals": {
        "high_rps": 200,
        "high_error_rate_pct": 20,
        "high_unique_ips": 50,
        "high_response_time_ms": 500,
    },
}

MALWARE_INDICATORS = {
    "keywords": [
        "botnet", "ransomware", "firmware_tamper", "data_exfiltration",
        "c2_beacon", "process_execution", "file_system_change",
        "compromised", "unauthorized_access", "credential_brute_force",
        "tampered", "cryptominer", "keylogger", "backdoor",
    ],
    "mitre_ttps": ["T0882", "T0875", "T0869"],  # Theft, Change State, Protocol
    "device_signals": {
        "compromised_count": 1,  # Any compromised device triggers
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph State & Workflow
# ═══════════════════════════════════════════════════════════════════════════════

class TriageState(BaseModel):
    """State for the Triage Agent LangGraph workflow."""
    messages: list = []
    context_summary: str = ""
    aggregated_stats: Dict[str, Any] = {}
    window_id: str = ""

    # Pre-classification results (rule-based)
    rule_based_category: str = "unknown"
    rule_based_confidence: float = 0.0
    rule_based_signals: Dict[str, Any] = {}

    # LLM classification results
    llm_category: str = "unknown"
    llm_confidence: float = 0.0
    llm_reasoning: str = ""

    # Final routing decision
    final_category: str = "unknown"
    final_confidence: float = 0.0
    severity_score: int = 0  # 0-10
    route_to: List[str] = []  # ["ddos_agent", "malware_agent", ...]
    triage_summary: str = ""


class TriageAgent:
    """
    LangGraph agent for Tier 1 SOC triage and alert classification.

    Workflow: Pre-Classify (rules) → LLM Classify → Route → Publish
    """

    def __init__(self, llm=None, model_registry=None):
        """
        Args:
            llm: Optional pre-configured LLM instance.
            model_registry: Optional ModelRegistry for multi-provider support.
        """
        self.llm = llm
        self.model_registry = model_registry
        self._init_llm()
        self.graph = self._create_graph()
        self.total_triaged = 0
        self.category_counts = {
            ThreatCategory.BENIGN: 0,
            ThreatCategory.DDOS: 0,
            ThreatCategory.MALWARE: 0,
            ThreatCategory.MULTI_VECTOR: 0,
            ThreatCategory.UNKNOWN: 0,
        }

    def _init_llm(self):
        """Initialize LLM from model registry or environment."""
        if self.llm:
            return

        try:
            if self.model_registry:
                self.llm = self.model_registry.get_llm()
            else:
                # Try model registry first
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "arena"))
                    from model_registry import ModelRegistry
                    registry = ModelRegistry()
                    self.llm = registry.get_llm()
                    logger.info("LLM initialized from ModelRegistry")
                except Exception:
                    # Fallback to Groq directly
                    try:
                        from langchain_groq import ChatGroq
                        api_key = os.getenv("GROQ_API_KEY", "")
                        if api_key:
                            self.llm = ChatGroq(
                                temperature=0,
                                model_name="llama3-8b-8192",
                                groq_api_key=api_key,
                            )
                            logger.info("LLM initialized from Groq directly")
                    except ImportError:
                        pass
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")

        if not self.llm:
            logger.warning("No LLM available — triage will use rule-based classification only")

    def _create_graph(self):
        """Create LangGraph workflow for triage."""
        workflow = StateGraph(TriageState)

        workflow.add_node("pre_classify", self._pre_classify)
        workflow.add_node("llm_classify", self._llm_classify)
        workflow.add_node("make_routing_decision", self._make_routing_decision)

        workflow.set_entry_point("pre_classify")
        workflow.add_edge("pre_classify", "llm_classify")
        workflow.add_edge("llm_classify", "make_routing_decision")
        workflow.add_edge("make_routing_decision", END)

        return workflow.compile()

    # ── Graph Nodes ────────────────────────────────────────────────────────

    def _pre_classify(self, state: TriageState) -> dict:
        """Rule-based pre-classification using statistical signals."""
        stats = state.aggregated_stats
        summary = state.context_summary.lower()
        signals = {}

        ddos_score = 0.0
        malware_score = 0.0

        # ── Keyword matching ──
        for kw in DDOS_INDICATORS["keywords"]:
            if kw in summary:
                ddos_score += 0.15
                signals[f"ddos_kw_{kw}"] = True

        for kw in MALWARE_INDICATORS["keywords"]:
            if kw in summary:
                malware_score += 0.15
                signals[f"malware_kw_{kw}"] = True

        # ── MITRE TTP matching ──
        attack_indicators = stats.get("attack_indicators", {})
        ttps = attack_indicators.get("mitre_ttps", [])
        for ttp in ttps:
            if ttp in DDOS_INDICATORS["mitre_ttps"]:
                ddos_score += 0.2
                signals[f"ddos_ttp_{ttp}"] = True
            if ttp in MALWARE_INDICATORS["mitre_ttps"]:
                malware_score += 0.2
                signals[f"malware_ttp_{ttp}"] = True

        # ── Network signal analysis ──
        net = stats.get("network_stats", {})
        thresholds = DDOS_INDICATORS["network_signals"]

        if net.get("max_rps", 0) > thresholds["high_rps"]:
            ddos_score += 0.25
            signals["high_rps"] = net["max_rps"]

        if net.get("error_rate_pct", 0) > thresholds["high_error_rate_pct"]:
            ddos_score += 0.15
            signals["high_error_rate"] = net["error_rate_pct"]

        if net.get("unique_source_ips", 0) > thresholds["high_unique_ips"]:
            ddos_score += 0.2
            signals["high_unique_ips"] = net["unique_source_ips"]

        if net.get("avg_response_time_ms", 0) > thresholds["high_response_time_ms"]:
            ddos_score += 0.1
            signals["high_response_time"] = net["avg_response_time_ms"]

        # ── Device signal analysis ──
        dev = stats.get("device_stats", {})
        if dev.get("compromised_count", 0) >= MALWARE_INDICATORS["device_signals"]["compromised_count"]:
            malware_score += 0.3
            signals["compromised_devices"] = dev["compromised_count"]

        # ── Determine category ──
        ddos_score = min(ddos_score, 1.0)
        malware_score = min(malware_score, 1.0)

        suspicious = stats.get("suspicious_events", 0)
        if suspicious == 0:
            category = ThreatCategory.BENIGN
            confidence = 0.9
        elif ddos_score > 0.3 and malware_score > 0.3:
            category = ThreatCategory.MULTI_VECTOR
            confidence = max(ddos_score, malware_score)
        elif ddos_score > malware_score:
            category = ThreatCategory.DDOS
            confidence = ddos_score
        elif malware_score > 0:
            category = ThreatCategory.MALWARE
            confidence = malware_score
        else:
            category = ThreatCategory.UNKNOWN
            confidence = 0.3

        return {
            "rule_based_category": category,
            "rule_based_confidence": round(confidence, 2),
            "rule_based_signals": signals,
        }

    def _llm_classify(self, state: TriageState) -> dict:
        """LLM-based classification for nuanced decision-making."""
        # Skip LLM if no suspicious events or no LLM available
        if state.rule_based_category == ThreatCategory.BENIGN:
            return {
                "llm_category": ThreatCategory.BENIGN,
                "llm_confidence": 0.95,
                "llm_reasoning": "No suspicious activity detected — rule-based pre-classification confirmed benign.",
            }

        if not self.llm:
            return {
                "llm_category": state.rule_based_category,
                "llm_confidence": state.rule_based_confidence,
                "llm_reasoning": "LLM unavailable — using rule-based classification only.",
            }

        # Build classification prompt
        prompt = self._build_classification_prompt(state)

        try:
            response = self.llm.invoke(prompt)
            parsed = self._parse_llm_response(response.content)
            return {
                "llm_category": parsed["category"],
                "llm_confidence": parsed["confidence"],
                "llm_reasoning": parsed["reasoning"],
            }
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return {
                "llm_category": state.rule_based_category,
                "llm_confidence": state.rule_based_confidence,
                "llm_reasoning": f"LLM classification failed ({e}) — falling back to rules.",
            }

    def _make_routing_decision(self, state: TriageState) -> dict:
        """Combine rule-based and LLM results into a final routing decision."""
        # Weighted combination: LLM gets priority if available
        if state.llm_category != ThreatCategory.UNKNOWN:
            final_category = state.llm_category
            final_confidence = state.llm_confidence
        else:
            final_category = state.rule_based_category
            final_confidence = state.rule_based_confidence

        # Determine severity score (0-10)
        severity = 0
        if final_category == ThreatCategory.BENIGN:
            severity = 0
        elif final_category == ThreatCategory.DDOS:
            severity = min(10, int(final_confidence * 8) + 2)
        elif final_category == ThreatCategory.MALWARE:
            severity = min(10, int(final_confidence * 8) + 3)
        elif final_category == ThreatCategory.MULTI_VECTOR:
            severity = min(10, int(final_confidence * 8) + 4)

        # Determine routing
        route_to = []
        if final_category == ThreatCategory.DDOS:
            route_to = ["ddos_detection_agent"]
        elif final_category == ThreatCategory.MALWARE:
            route_to = ["malware_detection_agent"]
        elif final_category == ThreatCategory.MULTI_VECTOR:
            route_to = ["ddos_detection_agent", "malware_detection_agent"]

        # Build triage summary
        triage_summary = (
            f"Triage result for window {state.window_id}: "
            f"Category={final_category.upper()}, Confidence={final_confidence:.0%}, "
            f"Severity={severity}/10. "
            f"Routing to: {', '.join(route_to) if route_to else 'none (benign)'}. "
            f"Rule signals: {list(state.rule_based_signals.keys())}. "
            f"LLM reasoning: {state.llm_reasoning}"
        )

        return {
            "final_category": final_category,
            "final_confidence": round(final_confidence, 2),
            "severity_score": severity,
            "route_to": route_to,
            "triage_summary": triage_summary,
        }

    # ── LLM Prompt Engineering ─────────────────────────────────────────────

    def _build_classification_prompt(self, state: TriageState) -> str:
        """Build the LLM classification prompt."""
        return f"""You are a Tier 1 SOC analyst triaging security events for a smart lighting grid in Mumbai, India.

CONTEXT SUMMARY FROM LOG INGESTION:
{state.context_summary}

PRE-CLASSIFICATION SIGNALS:
- Rule-based category: {state.rule_based_category}
- Rule-based confidence: {state.rule_based_confidence}
- Signals detected: {json.dumps(state.rule_based_signals, indent=2)}

YOUR TASK:
Classify this event window into exactly ONE category:
1. "benign" — Normal traffic, no security concern
2. "ddos" — DDoS or volumetric network attack (HTTP flood, SYN flood, UDP flood, slowloris, DNS amplification)
3. "malware" — Malware, ransomware, botnet, firmware tampering, or data exfiltration
4. "multi_vector" — Combined network + host-level attack

RESPOND IN THIS EXACT JSON FORMAT (no other text):
{{
    "category": "<benign|ddos|malware|multi_vector>",
    "confidence": <0.0 to 1.0>,
    "reasoning": "<one sentence explaining your decision>"
}}"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()

            parsed = json.loads(response)
            category = parsed.get("category", "unknown").lower()
            valid_categories = [ThreatCategory.BENIGN, ThreatCategory.DDOS,
                                ThreatCategory.MALWARE, ThreatCategory.MULTI_VECTOR]
            if category not in valid_categories:
                category = ThreatCategory.UNKNOWN

            return {
                "category": category,
                "confidence": float(parsed.get("confidence", 0.5)),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return {
                "category": ThreatCategory.UNKNOWN,
                "confidence": 0.3,
                "reasoning": f"Failed to parse LLM response: {response[:100]}",
            }

    # ── Public API ─────────────────────────────────────────────────────────

    def triage(self, context_summary: str, aggregated_stats: Dict[str, Any],
               window_id: str = "") -> Dict[str, Any]:
        """
        Triage a context summary from the Log Ingestion Agent.

        Args:
            context_summary: Natural language summary from ContextSummaryGenerator
            aggregated_stats: Statistical aggregation from StatisticalAggregator
            window_id: Identifier for the event window

        Returns:
            Dict with routing decision, confidence, severity, and reasoning
        """
        initial_state = TriageState(
            context_summary=context_summary,
            aggregated_stats=aggregated_stats,
            window_id=window_id,
        )

        result = self.graph.invoke(initial_state)

        self.total_triaged += 1
        category = result.get("final_category", ThreatCategory.UNKNOWN)
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

        return {
            "window_id": window_id,
            "category": result.get("final_category"),
            "confidence": result.get("final_confidence"),
            "severity_score": result.get("severity_score"),
            "route_to": result.get("route_to"),
            "triage_summary": result.get("triage_summary"),
            "rule_based": {
                "category": result.get("rule_based_category"),
                "confidence": result.get("rule_based_confidence"),
                "signals": result.get("rule_based_signals"),
            },
            "llm_based": {
                "category": result.get("llm_category"),
                "confidence": result.get("llm_confidence"),
                "reasoning": result.get("llm_reasoning"),
            },
        }

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "total_triaged": self.total_triaged,
            "category_counts": self.category_counts,
            "llm_available": self.llm is not None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Demo & CLI
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Run a demo triage with synthetic data."""
    agent = TriageAgent()

    # Simulate a suspicious context summary (from log ingestion agent)
    context_summary = """=== SECURITY EVENT WINDOW: W1708800000 ===
Period: 2025-02-24T12:00:00 to 2025-02-24T12:00:30
Total events: 85 (2.8 events/sec)

ZONE ACTIVITY:
  bkc_commercial: 55 events
  reliance_hospital: 20 events
  airport: 10 events

⚠ SUSPICIOUS EVENTS: 15 (17.6% of total)
  Attack types detected: http_flood(15)
  MITRE ATT&CK TTPs: T0813, T0883
  Attack stages: N/A

NETWORK TRAFFIC (65 events):
  Protocols: {'HTTP': 45, 'HTTPS': 10, 'MQTT': 10}
  Unique source IPs: 42
  Max RPS observed: 650
  Avg response time: 1250.0ms (max: 4800.0ms)
  Error rate: 25.0%
  Data volume: 12000B sent, 3000B received
  Top source IPs: 45.121.33.4(5), 91.235.116.100(3), 185.220.101.42(3)

SENSOR DATA (20 readings):
  Avg ambient: 250.0 lux, Avg power: 150.0W, Motion detections: 6

SEVERITY DISTRIBUTION: {'3': 50, '7': 15, '0': 20}
"""

    stats = {
        "total_events": 85,
        "suspicious_events": 15,
        "suspicious_pct": 17.6,
        "network_stats": {
            "count": 65,
            "max_rps": 650,
            "error_rate_pct": 25.0,
            "unique_source_ips": 42,
            "avg_response_time_ms": 1250.0,
        },
        "device_stats": {"count": 0, "compromised_count": 0},
        "attack_indicators": {
            "detected": True,
            "count": 15,
            "attack_types": {"http_flood": 15},
            "mitre_ttps": ["T0813", "T0883"],
        },
    }

    result = agent.triage(context_summary, stats, "W1708800000")

    print(f"\n{'='*70}")
    print(f"  TRIAGE AGENT — Demo Results")
    print(f"{'='*70}")
    print(f"  Category: {result['category'].upper()}")
    print(f"  Confidence: {result['confidence']:.0%}")
    print(f"  Severity: {result['severity_score']}/10")
    print(f"  Route to: {', '.join(result['route_to'])}")
    print(f"\n  Rule-based: {result['rule_based']['category']} "
          f"({result['rule_based']['confidence']:.0%})")
    print(f"  LLM-based: {result['llm_based']['category']} "
          f"({result['llm_based']['confidence']:.0%})")
    print(f"  LLM reasoning: {result['llm_based']['reasoning']}")
    print(f"\n  Triage Summary:")
    print(f"  {result['triage_summary']}")
    print(f"{'='*70}\n")

    return result


if __name__ == "__main__":
    demo()
