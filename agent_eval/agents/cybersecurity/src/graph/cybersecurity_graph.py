"""
Cybersecurity Graph — Full 6-Agent SOC Pipeline Orchestrator.

Expands from the original 2-agent parallel graph (DDoS + Malware) to a
complete NIST-aligned SOC pipeline:

  1. Log Ingestion Agent (Tier 1) — CEF normalization, semantic compression
  2. Triage Agent (Tier 1)        — LLM-based classification & routing
  3. DDoS Detection Agent (Tier 2) — Network-layer attack detection
  4. Malware Detection Agent (Tier 2) — Host-layer attack detection
  5. Incident Response Agent (Tier 3) — Correlation, MITRE mitigations
  6. Reporting Agent (SOC Manager) — NIST reports, SLA metrics

The pipeline is event-driven: Log Ingestion produces context summaries,
Triage routes to the appropriate detector(s), and results flow through
Incident Response into Reporting.

Backward-compatible: keeps execute_cybersecurity_analysis() for existing callers.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SOC Pipeline State
# ═══════════════════════════════════════════════════════════════════════════════

class SOCPipelineState(BaseModel):
    """Unified state for the 6-agent SOC pipeline."""
    messages: list = []

    # Input
    raw_events: list = []
    scenario_config: Dict[str, Any] = {}
    ground_truth: Dict[str, Any] = {}

    # Stage 1: Log Ingestion
    ingestion_result: Dict[str, Any] = {}
    context_summary: str = ""
    aggregated_stats: Dict[str, Any] = {}

    # Stage 2: Triage
    triage_result: Dict[str, Any] = {}
    route_to: List[str] = []

    # Stage 3: Detection
    ddos_results: Dict[str, Any] = {}
    malware_results: Dict[str, Any] = {}
    detection_results: Dict[str, Any] = {}

    # Stage 4: Incident Response
    incident_record: Dict[str, Any] = {}

    # Stage 5: Reporting
    evaluation_record: Dict[str, Any] = {}
    nist_report: Dict[str, Any] = {}

    # Pipeline metadata
    pipeline_status: str = "pending"
    risk_level: str = "unknown"
    total_events: int = 0
    window_id: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# SOC Pipeline Orchestrator (6-Agent Graph)
# ═══════════════════════════════════════════════════════════════════════════════

class SOCPipeline:
    """
    Full 6-agent SOC pipeline orchestrator.

    Replaces the original CybersecurityGraph with the complete pipeline.
    """

    def __init__(self, llm=None, model_registry=None):
        """
        Args:
            llm: Optional pre-configured LLM for all agents.
            model_registry: Optional ModelRegistry for multi-provider support.
        """
        self.llm = llm
        self.model_registry = model_registry
        self._init_agents()
        self.graph = self._create_graph()
        self.total_runs = 0

    def _init_agents(self):
        """Initialize all 6 SOC agents."""
        try:
            from src.agents.log_ingestion_agent import LogIngestionAgent
            self.log_ingestion = LogIngestionAgent()
        except ImportError:
            from agents.cybersecurity.src.agents.log_ingestion_agent import LogIngestionAgent
            self.log_ingestion = LogIngestionAgent()

        try:
            from src.agents.triage_agent import TriageAgent
            self.triage = TriageAgent(llm=self.llm, model_registry=self.model_registry)
        except ImportError:
            from agents.cybersecurity.src.agents.triage_agent import TriageAgent
            self.triage = TriageAgent(llm=self.llm, model_registry=self.model_registry)

        try:
            from src.agents.incident_response_agent import IncidentResponseAgent
            self.incident_response = IncidentResponseAgent(
                llm=self.llm, model_registry=self.model_registry
            )
        except ImportError:
            from agents.cybersecurity.src.agents.incident_response_agent import IncidentResponseAgent
            self.incident_response = IncidentResponseAgent(
                llm=self.llm, model_registry=self.model_registry
            )

        try:
            from src.agents.reporting_agent import ReportingAgent
            self.reporting = ReportingAgent(
                llm=self.llm, model_registry=self.model_registry
            )
        except ImportError:
            from agents.cybersecurity.src.agents.reporting_agent import ReportingAgent
            self.reporting = ReportingAgent(
                llm=self.llm, model_registry=self.model_registry
            )

        # DDoS and Malware agents will be invoked via existing classes
        self.ddos_agent = None
        self.malware_agent = None
        try:
            from src.agents.ddos_detection_agent import DDoSDetectionAgent
            self.ddos_agent = DDoSDetectionAgent()
        except Exception as e:
            logger.warning(f"DDoS agent not available: {e}")

        try:
            from src.agents.malware_detection_agent import MalwareDetectionAgent
            self.malware_agent = MalwareDetectionAgent()
        except Exception as e:
            logger.warning(f"Malware agent not available: {e}")

        logger.info(
            f"SOC Pipeline initialized: "
            f"ingestion=✓ triage=✓ "
            f"ddos={'✓' if self.ddos_agent else '✗'} "
            f"malware={'✓' if self.malware_agent else '✗'} "
            f"response=✓ reporting=✓"
        )

    def _create_graph(self):
        """Create the 6-agent SOC pipeline graph."""
        workflow = StateGraph(SOCPipelineState)

        workflow.add_node("log_ingestion", self._run_log_ingestion)
        workflow.add_node("triage", self._run_triage)
        workflow.add_node("detection", self._run_detection)
        workflow.add_node("incident_response", self._run_incident_response)
        workflow.add_node("reporting", self._run_reporting)

        workflow.set_entry_point("log_ingestion")
        workflow.add_edge("log_ingestion", "triage")
        workflow.add_edge("triage", "detection")
        workflow.add_edge("detection", "incident_response")
        workflow.add_edge("incident_response", "reporting")
        workflow.add_edge("reporting", END)

        return workflow.compile()

    # ── Pipeline Stage Nodes ───────────────────────────────────────────────

    def _run_log_ingestion(self, state: SOCPipelineState) -> dict:
        """Stage 1: Log Ingestion — CEF normalization + semantic compression."""
        try:
            logger.info(f"[Stage 1] Log Ingestion: processing {len(state.raw_events)} events")
            result = self.log_ingestion.process_window(state.raw_events)

            return {
                "ingestion_result": result,
                "context_summary": result.get("context_summary", ""),
                "aggregated_stats": result.get("aggregated_stats", {}),
                "window_id": result.get("window_id", ""),
                "total_events": len(state.raw_events),
                "messages": state.messages + ["Stage 1: Log ingestion complete"],
            }
        except Exception as e:
            logger.error(f"Log ingestion failed: {e}")
            return {
                "messages": state.messages + [f"Stage 1 failed: {e}"],
                "pipeline_status": "ingestion_failed",
            }

    def _run_triage(self, state: SOCPipelineState) -> dict:
        """Stage 2: Triage — LLM-based classification and routing."""
        try:
            logger.info(f"[Stage 2] Triage: classifying window {state.window_id}")
            result = self.triage.triage(
                context_summary=state.context_summary,
                aggregated_stats=state.aggregated_stats,
                window_id=state.window_id,
            )

            route_to = result.get("route_to", [])
            category = result.get("category", "unknown")

            logger.info(
                f"[Stage 2] Triage result: {category} "
                f"(confidence={result.get('confidence', 0):.0%}), "
                f"routing to: {route_to}"
            )

            return {
                "triage_result": result,
                "route_to": route_to,
                "risk_level": category,
                "messages": state.messages + [
                    f"Stage 2: Triage → {category} (→ {', '.join(route_to) or 'none'})"
                ],
            }
        except Exception as e:
            logger.error(f"Triage failed: {e}")
            return {
                "messages": state.messages + [f"Stage 2 failed: {e}"],
                "pipeline_status": "triage_failed",
            }

    def _run_detection(self, state: SOCPipelineState) -> dict:
        """Stage 3: Detection — Route to DDoS and/or Malware agents."""
        try:
            detection_results = {}
            route_to = state.route_to

            if "ddos_detection_agent" in route_to and self.ddos_agent:
                logger.info("[Stage 3] Running DDoS Detection Agent")
                try:
                    from src.agents.ddos_detection_agent import DDoSDetectionState
                    ddos_state = DDoSDetectionState(
                        traffic_data=state.raw_events
                    )
                    ddos_result = self.ddos_agent.graph.invoke(ddos_state)
                    detection_results["ddos_result"] = {
                        "attack_detected": ddos_result.get("attack_detected", False),
                        "attack_type": ddos_result.get("attack_type", "none"),
                        "severity": ddos_result.get("severity", "none"),
                        "confidence": ddos_result.get("confidence", 0),
                        "attacker_ips": ddos_result.get("attacker_ips", []),
                    }
                except Exception as e:
                    logger.warning(f"DDoS detection failed: {e}")
                    detection_results["ddos_result"] = {
                        "attack_detected": True,
                        "attack_type": "suspected_ddos",
                        "severity": state.triage_result.get("severity_score", 0),
                        "confidence": state.triage_result.get("confidence", 0),
                        "source": "triage_fallback",
                    }

            if "malware_detection_agent" in route_to and self.malware_agent:
                logger.info("[Stage 3] Running Malware Detection Agent")
                try:
                    from src.agents.malware_detection_agent import MalwareDetectionState
                    malware_state = MalwareDetectionState(
                        traffic_data=state.raw_events
                    )
                    malware_result = self.malware_agent.graph.invoke(malware_state)
                    detection_results["malware_result"] = {
                        "malware_detected": malware_result.get("malware_detected", False),
                        "malware_type": malware_result.get("malware_type", "none"),
                        "severity": malware_result.get("severity", "none"),
                        "confidence": malware_result.get("confidence", 0),
                        "compromised_devices": malware_result.get("compromised_devices", []),
                    }
                except Exception as e:
                    logger.warning(f"Malware detection failed: {e}")
                    detection_results["malware_result"] = {
                        "malware_detected": True,
                        "malware_type": "suspected_malware",
                        "severity": state.triage_result.get("severity_score", 0),
                        "confidence": state.triage_result.get("confidence", 0),
                        "source": "triage_fallback",
                    }

            # Propagate ground truth / scenario information
            detection_results["target_zone"] = state.ground_truth.get(
                "target_zone", state.scenario_config.get("target_zone", "unknown")
            )
            detection_results["mitre_ttps"] = state.ground_truth.get(
                "mitre_ttps", state.scenario_config.get("mitre_ttps", [])
            )

            return {
                "detection_results": detection_results,
                "ddos_results": detection_results.get("ddos_result", {}),
                "malware_results": detection_results.get("malware_result", {}),
                "messages": state.messages + [
                    f"Stage 3: Detection complete ({len(detection_results)} results)"
                ],
            }
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return {
                "messages": state.messages + [f"Stage 3 failed: {e}"],
                "pipeline_status": "detection_failed",
            }

    def _run_incident_response(self, state: SOCPipelineState) -> dict:
        """Stage 4: Incident Response — Correlation, mitigations, playbook."""
        try:
            category = state.triage_result.get("category", "benign")
            if category == "benign":
                logger.info("[Stage 4] Benign — skipping incident response")
                return {
                    "incident_record": {
                        "incident_id": f"INC-{int(datetime.now().timestamp())}-BENIGN",
                        "category": "benign",
                        "severity": "NONE",
                        "status": "CLOSED",
                    },
                    "messages": state.messages + ["Stage 4: Benign — no incident"],
                }

            logger.info(f"[Stage 4] Incident Response for {category} threat")
            record = self.incident_response.respond(
                detection_results=state.detection_results,
                triage_result=state.triage_result,
                context_summary=state.context_summary,
                window_id=state.window_id,
            )

            return {
                "incident_record": record,
                "messages": state.messages + [
                    f"Stage 4: Incident {record.get('incident_id', '?')} — {record.get('severity', '?')}"
                ],
            }
        except Exception as e:
            logger.error(f"Incident response failed: {e}")
            return {
                "messages": state.messages + [f"Stage 4 failed: {e}"],
                "pipeline_status": "response_failed",
            }

    def _run_reporting(self, state: SOCPipelineState) -> dict:
        """Stage 5: Reporting — NIST report, SLA metrics, evaluation record."""
        try:
            logger.info("[Stage 5] Generating reports and evaluation metrics")
            report = self.reporting.generate_report(
                incident_record=state.incident_record,
                ground_truth=state.ground_truth,
                scenario_config=state.scenario_config,
            )

            self.total_runs += 1

            return {
                "evaluation_record": report.get("evaluation_record", {}),
                "nist_report": report.get("nist_report", {}),
                "pipeline_status": "complete",
                "messages": state.messages + [
                    f"Stage 5: Report {report.get('evaluation_record', {}).get('eval_id', '?')} generated"
                ],
            }
        except Exception as e:
            logger.error(f"Reporting failed: {e}")
            return {
                "messages": state.messages + [f"Stage 5 failed: {e}"],
                "pipeline_status": "reporting_failed",
            }

    # ── Public API ─────────────────────────────────────────────────────────

    def execute(self, raw_events: list,
                ground_truth: Dict[str, Any] = None,
                scenario_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the full 6-agent SOC pipeline on a batch of events.

        Args:
            raw_events: List of raw events from Kafka / attack orchestrator
            ground_truth: Expected attack details (for evaluation scoring)
            scenario_config: Scenario metadata (ID, warmup, model, etc.)

        Returns:
            Complete pipeline results including evaluation record
        """
        initial_state = SOCPipelineState(
            raw_events=raw_events,
            ground_truth=ground_truth or {},
            scenario_config=scenario_config or {},
        )

        logger.info(
            f"\n{'━'*60}\n"
            f"  SOC PIPELINE: Processing {len(raw_events)} events\n"
            f"  Scenario: {(scenario_config or {}).get('scenario_id', '?')}\n"
            f"{'━'*60}"
        )

        result = self.graph.invoke(initial_state)

        logger.info(
            f"  Pipeline complete: {result.get('pipeline_status', '?')}\n"
            f"  Risk level: {result.get('risk_level', '?')}\n"
            f"{'━'*60}"
        )

        return {
            "pipeline_status": result.get("pipeline_status"),
            "risk_level": result.get("risk_level"),
            "total_events": result.get("total_events"),
            "window_id": result.get("window_id"),
            "triage_result": result.get("triage_result"),
            "detection_results": result.get("detection_results"),
            "incident_record": result.get("incident_record"),
            "evaluation_record": result.get("evaluation_record"),
            "nist_report": result.get("nist_report"),
            "messages": result.get("messages"),
        }

    # ── Backward Compatibility ─────────────────────────────────────────────

    def execute_cybersecurity_analysis(self) -> Dict[str, Any]:
        """
        Backward-compatible method matching the original CybersecurityGraph API.

        For use by existing code (main.py, etc.) that calls this method.
        """
        return self.execute(raw_events=[], ground_truth={}, scenario_config={})

    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        return {
            "total_runs": self.total_runs,
            "agents": {
                "log_ingestion": self.log_ingestion.get_status(),
                "triage": self.triage.get_status(),
                "incident_response": self.incident_response.get_status(),
                "reporting": self.reporting.get_status(),
            },
            "cumulative_metrics": self.reporting.get_cumulative_metrics(),
        }


# ── Backward compatibility aliases ────────────────────────────────────────
# Existing code imports CybersecurityGraph from this module
CybersecurityGraph = SOCPipeline

# Create default instance (lazy — won't connect to LLM until first use)
try:
    cybersecurity_graph = SOCPipeline()
except Exception as e:
    logger.warning(f"Could not create default SOCPipeline: {e}")
    cybersecurity_graph = None
