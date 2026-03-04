"""
Incident Response Agent — Tier 3 SOC: Correlation, MITRE mitigations, playbook execution.

Receives detection results from DDoS and Malware agents and:
  1. Correlates multiple detections across zones and time windows
  2. Maps attacks to MITRE ATT&CK for ICS mitigations
  3. Generates zone-adaptive response actions (IEC 62443 security levels)
  4. Executes automated response playbooks
  5. Produces structured incident records for the Reporting Agent

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
logger = logging.getLogger("incident-response-agent")


# ═══════════════════════════════════════════════════════════════════════════════
# MITRE ATT&CK for ICS Mitigations
# ═══════════════════════════════════════════════════════════════════════════════

MITRE_MITIGATIONS = {
    "T0883": {
        "name": "Internet Accessible Device",
        "mitigations": {
            "M0930": "Network Segmentation — Isolate exposed devices behind DMZ/firewall.",
            "M0813": "Access Management — Restrict internet-facing services to required ports.",
            "M0927": "Communication Authenticity — Enforce TLS/mTLS on all external APIs.",
        },
    },
    "T0804": {
        "name": "Unauthorized Command Message",
        "mitigations": {
            "M0802": "Communication Authenticity — Validate all command sources.",
            "M0937": "Supervision — Enable real-time monitoring of command channels.",
        },
    },
    "T0813": {
        "name": "Denial of Control",
        "mitigations": {
            "M0810": "Out-of-Band Channel — Maintain backup control paths.",
            "M0953": "Redundancy — Deploy failover lighting controllers in critical zones.",
            "M0930": "Network Segmentation — Segment control plane from data plane.",
        },
    },
    "T0834": {
        "name": "Loss of Productivity and Revenue",
        "mitigations": {
            "M0953": "Redundancy — Automated failover to backup systems.",
            "M0810": "Out-of-Band Channel — Emergency manual lighting controls.",
        },
    },
    "T0882": {
        "name": "Theft of Operational Information",
        "mitigations": {
            "M0932": "Credential Protection — Rotate default SNMP/SSH credentials.",
            "M0927": "Communication Authenticity — Enforce mutual authentication.",
            "M0801": "Access Management — Implement role-based access control.",
        },
    },
    "T0875": {
        "name": "Change Program State",
        "mitigations": {
            "M0947": "Software Process and Device Integrity — Firmware signing/validation.",
            "M0937": "Supervision — Monitor for unauthorized state changes.",
            "M0801": "Access Management — Restrict write access to authorized operators.",
        },
    },
    "T0869": {
        "name": "Standard Application Layer Protocol",
        "mitigations": {
            "M0931": "Network Intrusion Prevention — Deploy IPS on C2 communication channels.",
            "M0930": "Network Segmentation — Block unauthorized outbound connections.",
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# IEC 62443 Zone-Adaptive Response Playbooks
# ═══════════════════════════════════════════════════════════════════════════════

ZONE_RESPONSE_PLAYBOOKS = {
    # Security Level 1 — Residential/Low-risk
    1: {
        "ddos": [
            "ALERT: Notify zone administrator via email/SMS.",
            "MONITOR: Increase sampling rate to 1-second intervals for 10 minutes.",
            "LOG: Record incident for monthly review.",
        ],
        "malware": [
            "ALERT: Notify zone administrator + IT security team.",
            "ISOLATE: Flag infected devices for manual review.",
            "LOG: Record incident with device identifiers.",
        ],
    },
    # Security Level 2 — Commercial/Highway
    2: {
        "ddos": [
            "ALERT: Notify SOC team immediately.",
            "BLOCK: Apply rate limiting on affected endpoints (50% reduction).",
            "REROUTE: Redirect traffic to scrubbing center if available.",
            "MONITOR: Increase monitoring to real-time for 30 minutes.",
        ],
        "malware": [
            "ALERT: Notify SOC team + CERT-In (if Indian critical infra).",
            "ISOLATE: Network-isolate compromised devices immediately.",
            "SCAN: Trigger full firmware integrity scan on zone devices.",
            "CREDENTIAL: Force credential rotation for affected zone.",
        ],
    },
    # Security Level 3 — Industrial/Port
    3: {
        "ddos": [
            "ALERT: SOC team + Zone controller emergency handler.",
            "BLOCK: Apply aggressive rate limiting (80% reduction).",
            "FAILOVER: Activate backup controller for zone operations.",
            "REROUTE: Redirect all traffic through DDoS mitigation proxy.",
            "REPORT: Generate preliminary incident report within 15 minutes.",
        ],
        "malware": [
            "ALERT: SOC team + CERT-In + Industrial control team.",
            "ISOLATE: Immediate network isolation of ALL compromised devices.",
            "FAILOVER: Switch to backup controllers.",
            "FORENSICS: Preserve device state for post-incident analysis.",
            "SCAN: Full zone-wide firmware + process integrity scan.",
        ],
    },
    # Security Level 4 — Hospital/Airport (Critical)
    4: {
        "ddos": [
            "CRITICAL ALERT: SOC team + Zone emergency + Management escalation.",
            "BLOCK: Immediate traffic blackhole for attack sources.",
            "FAILOVER: Activate ALL backup controllers and secondary data paths.",
            "MANUAL: Enable emergency manual lighting controls for patient/passenger safety.",
            "REROUTE: Full traffic diversion to DDoS scrubbing infrastructure.",
            "REPORT: Generate incident report within 5 minutes for compliance.",
            "CERT-IN: Notify CERT-In within 6 hours (Indian regulatory requirement).",
        ],
        "malware": [
            "CRITICAL ALERT: SOC team + CERT-In + Hospital IT/Airport authority.",
            "ISOLATE: Immediate physical + network isolation of compromised devices.",
            "FAILOVER: Emergency failover to isolated backup systems.",
            "MANUAL: Enable emergency manual controls for critical areas.",
            "FORENSICS: Full forensic capture (memory, disk, network).",
            "CREDENTIAL: Emergency credential rotation across zone.",
            "REPORT: Generate NIST-compliant incident report within 5 minutes.",
            "CERT-IN: Mandatory notification to CERT-In within 6 hours.",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph State & Agent
# ═══════════════════════════════════════════════════════════════════════════════

class IncidentResponseState(BaseModel):
    """State for the Incident Response Agent."""
    messages: list = []
    detection_results: Dict[str, Any] = {}
    triage_result: Dict[str, Any] = {}
    context_summary: str = ""
    window_id: str = ""

    # Correlation results
    correlated_detections: List[Dict[str, Any]] = []
    attack_timeline: List[Dict[str, Any]] = []

    # Response planning
    mitre_mitigations: List[Dict[str, Any]] = []
    playbook_actions: List[str] = []
    severity_level: str = "LOW"
    zone_security_level: int = 1

    # LLM-generated response
    llm_response_plan: str = ""

    # Final incident record
    incident_record: Dict[str, Any] = {}


class IncidentResponseAgent:
    """
    LangGraph agent for Tier 3 SOC incident response.

    Workflow: Correlate → Map Mitigations → Plan Response → Generate Record
    """

    def __init__(self, llm=None, model_registry=None):
        self.llm = llm
        self.model_registry = model_registry
        self._init_llm()
        self.graph = self._create_graph()
        self.incidents: List[Dict[str, Any]] = []
        self.total_incidents = 0

    def _init_llm(self):
        """Initialize LLM from model registry or environment."""
        if self.llm:
            return
        try:
            if self.model_registry:
                self.llm = self.model_registry.get_llm()
            else:
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "arena"))
                    from model_registry import ModelRegistry
                    registry = ModelRegistry()
                    self.llm = registry.get_llm()
                except Exception:
                    try:
                        from langchain_groq import ChatGroq
                        api_key = os.getenv("GROQ_API_KEY", "")
                        if api_key:
                            self.llm = ChatGroq(
                                temperature=0,
                                model_name="llama3-8b-8192",
                                groq_api_key=api_key,
                            )
                    except ImportError:
                        pass
        except Exception as e:
            logger.warning(f"Could not initialize LLM: {e}")

    def _create_graph(self):
        """Create LangGraph workflow for incident response."""
        workflow = StateGraph(IncidentResponseState)

        workflow.add_node("correlate_detections", self._correlate_detections)
        workflow.add_node("map_mitigations", self._map_mitigations)
        workflow.add_node("generate_playbook", self._generate_playbook)
        workflow.add_node("llm_response_planning", self._llm_response_planning)
        workflow.add_node("create_incident_record", self._create_incident_record)

        workflow.set_entry_point("correlate_detections")
        workflow.add_edge("correlate_detections", "map_mitigations")
        workflow.add_edge("map_mitigations", "generate_playbook")
        workflow.add_edge("generate_playbook", "llm_response_planning")
        workflow.add_edge("llm_response_planning", "create_incident_record")
        workflow.add_edge("create_incident_record", END)

        return workflow.compile()

    # ── Graph Nodes ────────────────────────────────────────────────────────

    def _correlate_detections(self, state: IncidentResponseState) -> dict:
        """Correlate detection results across agents and time windows."""
        detections = state.detection_results
        triage = state.triage_result

        # Build attack timeline
        timeline = []
        attack_category = triage.get("category", "unknown")
        severity = triage.get("severity_score", 0)

        # Map severity score to level
        if severity >= 8:
            severity_level = "CRITICAL"
        elif severity >= 6:
            severity_level = "HIGH"
        elif severity >= 4:
            severity_level = "MEDIUM"
        else:
            severity_level = "LOW"

        # Determine zone security level from triage or detection
        zone_id = detections.get("target_zone", "unknown")
        zone_sl = self._get_zone_security_level(zone_id)

        # Create timeline entry
        timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": f"Attack detected: {attack_category}",
            "severity": severity_level,
            "zone": zone_id,
            "confidence": triage.get("confidence", 0),
            "details": detections,
        })

        correlated = [{
            "source": "triage_agent",
            "category": attack_category,
            "confidence": triage.get("confidence", 0),
            "zone": zone_id,
        }]

        # Add DDoS detection correlation
        if "ddos_result" in detections:
            ddos = detections["ddos_result"]
            correlated.append({
                "source": "ddos_detection_agent",
                "attack_type": ddos.get("attack_type", "unknown"),
                "confidence": ddos.get("confidence", 0),
                "attacker_ips": ddos.get("attacker_ips", []),
            })
            timeline.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": f"DDoS detection: {ddos.get('attack_type', '?')}",
                "severity": severity_level,
                "details": ddos,
            })

        # Add Malware detection correlation
        if "malware_result" in detections:
            mlw = detections["malware_result"]
            correlated.append({
                "source": "malware_detection_agent",
                "malware_type": mlw.get("malware_type", "unknown"),
                "confidence": mlw.get("confidence", 0),
                "compromised_devices": mlw.get("compromised_devices", []),
            })
            timeline.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": f"Malware detection: {mlw.get('malware_type', '?')}",
                "severity": severity_level,
                "details": mlw,
            })

        return {
            "correlated_detections": correlated,
            "attack_timeline": timeline,
            "severity_level": severity_level,
            "zone_security_level": zone_sl,
        }

    def _map_mitigations(self, state: IncidentResponseState) -> dict:
        """Map detected TTPs to MITRE ATT&CK for ICS mitigations."""
        triage = state.triage_result
        detections = state.detection_results
        mitigations = []

        # Collect TTPs from detection results
        ttps = set()
        if "mitre_ttps" in detections:
            ttps.update(detections["mitre_ttps"])
        if "mitre_ttps" in triage:
            ttps.update(triage["mitre_ttps"])

        for ttp in ttps:
            if ttp in MITRE_MITIGATIONS:
                info = MITRE_MITIGATIONS[ttp]
                for mid, desc in info["mitigations"].items():
                    mitigations.append({
                        "ttp": ttp,
                        "ttp_name": info["name"],
                        "mitigation_id": mid,
                        "description": desc,
                    })

        # Deduplicate by mitigation ID
        seen = set()
        unique_mitigations = []
        for m in mitigations:
            if m["mitigation_id"] not in seen:
                seen.add(m["mitigation_id"])
                unique_mitigations.append(m)

        return {"mitre_mitigations": unique_mitigations}

    def _generate_playbook(self, state: IncidentResponseState) -> dict:
        """Generate zone-adaptive response playbook actions."""
        category = state.triage_result.get("category", "unknown")
        sl = state.zone_security_level

        # Map category to playbook key
        if category in ("ddos", "multi_vector"):
            playbook_key = "ddos"
        elif category == "malware":
            playbook_key = "malware"
        else:
            return {"playbook_actions": ["MONITOR: Continue standard monitoring."]}

        # Get zone-appropriate playbook
        playbooks = ZONE_RESPONSE_PLAYBOOKS.get(sl, ZONE_RESPONSE_PLAYBOOKS[1])
        actions = playbooks.get(playbook_key, ["ALERT: Notify SOC team."])

        return {"playbook_actions": list(actions)}

    def _llm_response_planning(self, state: IncidentResponseState) -> dict:
        """Use LLM to generate a contextual response plan."""
        if not self.llm:
            return {"llm_response_plan": "LLM unavailable — using pre-defined playbook actions."}

        prompt = f"""You are a Tier 3 SOC incident responder for Mumbai's smart lighting grid.

INCIDENT DETAILS:
- Severity: {state.severity_level}
- Zone Security Level: SL-{state.zone_security_level} (IEC 62443)
- Category: {state.triage_result.get('category', 'unknown')}
- Confidence: {state.triage_result.get('confidence', 0):.0%}

CONTEXT:
{state.context_summary[:800]}

CORRELATED DETECTIONS:
{json.dumps(state.correlated_detections, indent=2, default=str)[:500]}

MITRE MITIGATIONS MAPPED:
{json.dumps([m['description'] for m in state.mitre_mitigations], indent=2)[:500]}

PRE-DEFINED PLAYBOOK ACTIONS:
{json.dumps(state.playbook_actions, indent=2)}

Generate a BRIEF incident response summary (3-5 sentences) covering:
1. What happened (attack type, scope)
2. Immediate actions taken
3. Recommended follow-up actions
4. Compliance/notification requirements (CERT-In if Indian critical infra)"""

        try:
            response = self.llm.invoke(prompt)
            return {"llm_response_plan": response.content}
        except Exception as e:
            logger.warning(f"LLM response planning failed: {e}")
            return {"llm_response_plan": f"Auto-generated (LLM failed): Execute playbook actions in sequence."}

    def _create_incident_record(self, state: IncidentResponseState) -> dict:
        """Create the final incident record."""
        record = {
            "incident_id": f"INC-{int(time.time())}-{self.total_incidents + 1:04d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "window_id": state.window_id,
            "severity": state.severity_level,
            "zone_security_level": f"SL-{state.zone_security_level}",
            "category": state.triage_result.get("category", "unknown"),
            "confidence": state.triage_result.get("confidence", 0),
            "attack_timeline": state.attack_timeline,
            "correlated_detections": state.correlated_detections,
            "mitre_mitigations": state.mitre_mitigations,
            "playbook_actions": state.playbook_actions,
            "response_plan": state.llm_response_plan,
            "status": "OPEN",
            "assigned_to": "SOC_TEAM",
        }

        self.incidents.append(record)
        self.total_incidents += 1

        return {"incident_record": record}

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _get_zone_security_level(zone_id: str) -> int:
        """Get IEC 62443 security level for a zone."""
        SL_MAP = {
            "bkc_commercial": 2,
            "reliance_hospital": 4,
            "airport": 4,
            "port_area": 3,
            "school_complex": 2,
            "residential": 1,
            "highway_corridor": 2,
        }
        return SL_MAP.get(zone_id, 2)

    # ── Public API ─────────────────────────────────────────────────────────

    def respond(self, detection_results: Dict[str, Any],
                triage_result: Dict[str, Any],
                context_summary: str = "",
                window_id: str = "") -> Dict[str, Any]:
        """
        Generate incident response for detection results.

        Args:
            detection_results: Results from DDoS/Malware detection agents
            triage_result: Triage classification from TriageAgent
            context_summary: Original context summary from LogIngestionAgent
            window_id: Event window identifier

        Returns:
            Incident record with response plan, mitigations, and playbook
        """
        initial_state = IncidentResponseState(
            detection_results=detection_results,
            triage_result=triage_result,
            context_summary=context_summary,
            window_id=window_id,
        )

        result = self.graph.invoke(initial_state)
        return result.get("incident_record", {})

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_incidents": self.total_incidents,
            "open_incidents": len([i for i in self.incidents if i.get("status") == "OPEN"]),
            "severity_breakdown": {
                s: len([i for i in self.incidents if i.get("severity") == s])
                for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            },
        }
