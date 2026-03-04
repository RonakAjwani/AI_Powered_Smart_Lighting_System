"""
Arena Controller — Orchestrates the complete AI Cyber Arena evaluation pipeline.

Responsibilities:
  1. Spawn/manage zone simulator containers (or run in-process for local mode)
  2. Execute attack scenarios via the AttackOrchestrator
  3. Swap LLM models between evaluation runs
  4. Collect agent detection results from Kafka
  5. Co-ordinate the full evaluation loop: for each model × each scenario

Usage:
    # Local mode (no Docker required):
    python -m arena.controller --mode local --scenario S2 --model llama-3.1-8b

    # Docker mode (full container orchestration):
    python -m arena.controller --mode docker --scenario all
"""

import os
import sys
import json
import time
import uuid
import logging
import subprocess
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("arena-controller")

# ── Imports from arena package ──
try:
    from arena.attack_orchestrator import AttackOrchestrator, ScenarioConfig, AttackPhase
    from arena.model_registry import ModelRegistry
except ImportError:
    # Running standalone — try relative
    try:
        from attack_orchestrator import AttackOrchestrator, ScenarioConfig, AttackPhase
        from model_registry import ModelRegistry
    except ImportError:
        logger.warning("Could not import arena modules, some features may be unavailable")

# ── Optional Kafka consumer ──
try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# ── Optional Redis ──
try:
    import redis as redis_lib
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# Zone Configuration — matches docker-compose.yml definitions
# ═══════════════════════════════════════════════════════════════════════════════

ZONE_CONFIGS = {
    "bkc_commercial": {
        "service_name": "zone-bkc",
        "name": "BKC Commercial",
        "num_poles": 8,
        "num_gateways": 2,
        "security_level": 2,
        "traffic_profile": "commercial_high",
    },
    "reliance_hospital": {
        "service_name": "zone-hospital",
        "name": "Reliance Hospital",
        "num_poles": 12,
        "num_gateways": 3,
        "security_level": 4,
        "traffic_profile": "critical_healthcare",
    },
    "airport": {
        "service_name": "zone-airport",
        "name": "CSM International Airport",
        "num_poles": 15,
        "num_gateways": 3,
        "security_level": 4,
        "traffic_profile": "critical_transport",
    },
    "port_area": {
        "service_name": "zone-port",
        "name": "Mumbai Port",
        "num_poles": 10,
        "num_gateways": 2,
        "security_level": 3,
        "traffic_profile": "industrial",
    },
    "school_complex": {
        "service_name": "zone-school",
        "name": "IIT Bombay School Complex",
        "num_poles": 6,
        "num_gateways": 1,
        "security_level": 2,
        "traffic_profile": "institutional",
    },
    "residential": {
        "service_name": "zone-residential",
        "name": "Bandra-Juhu Residential",
        "num_poles": 10,
        "num_gateways": 2,
        "security_level": 1,
        "traffic_profile": "residential",
    },
    "highway_corridor": {
        "service_name": "zone-highway",
        "name": "Western Express Highway",
        "num_poles": 20,
        "num_gateways": 4,
        "security_level": 2,
        "traffic_profile": "highway",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Built-in Scenario Library (matches implementation plan S1-S7, M1-M4)
# ═══════════════════════════════════════════════════════════════════════════════

BUILTIN_SCENARIOS = {
    "S1": ScenarioConfig(
        scenario_id="S1",
        name="Baseline — Normal Traffic",
        description="No attack. Generates only normal zone traffic to establish FPR baseline.",
        target_zone="bkc_commercial",
        target_zone_name="BKC Commercial",
        security_level=2,
        severity="NONE",
        total_duration_sec=120,
        warmup_sec=120,
        cooldown_sec=0,
        phases=[],
        ground_truth={"attack_type": "none", "severity": "NONE"},
        mitre_ttps=[],
    ),
    "S2": ScenarioConfig(
        scenario_id="S2",
        name="HTTP Flood on BKC Commercial",
        description="Layer 7 HTTP flood targeting BKC lighting API. India's financial sector was primary DDoS target in 2024.",
        target_zone="bkc_commercial",
        target_zone_name="BKC Commercial",
        security_level=2,
        severity="HIGH",
        total_duration_sec=120,
        warmup_sec=20,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="http_flood", start_offset_sec=0,
                        duration_sec=90, intensity=0.8, events_per_second=30),
        ],
        ground_truth={
            "attack_type": "DDoS/HTTP Flood",
            "severity": "HIGH",
            "target_zone": "bkc_commercial",
        },
        mitre_ttps=["T0883", "T0804", "T0813"],
    ),
    "S3": ScenarioConfig(
        scenario_id="S3",
        name="SYN Flood on Reliance Hospital",
        description="Layer 4 SYN flood on hospital zone. AIIMS Delhi 2022 showed hospitals are high-value targets.",
        target_zone="reliance_hospital",
        target_zone_name="Reliance Hospital",
        security_level=4,
        severity="CRITICAL",
        total_duration_sec=120,
        warmup_sec=15,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="syn_flood", start_offset_sec=0,
                        duration_sec=95, intensity=0.9, events_per_second=40),
        ],
        ground_truth={
            "attack_type": "DDoS/SYN Flood",
            "severity": "CRITICAL",
            "target_zone": "reliance_hospital",
        },
        mitre_ttps=["T0883", "T0813", "T0834"],
    ),
    "S4": ScenarioConfig(
        scenario_id="S4",
        name="UDP Flood on Airport",
        description="Volumetric UDP flood on airport zone. Critical transport infrastructure (SL-4).",
        target_zone="airport",
        target_zone_name="CSM International Airport",
        security_level=4,
        severity="CRITICAL",
        total_duration_sec=120,
        warmup_sec=15,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="udp_flood", start_offset_sec=0,
                        duration_sec=95, intensity=0.85, events_per_second=35),
        ],
        ground_truth={
            "attack_type": "DDoS/UDP Flood",
            "severity": "CRITICAL",
            "target_zone": "airport",
        },
        mitre_ttps=["T0883", "T0813"],
    ),
    "S5": ScenarioConfig(
        scenario_id="S5",
        name="Slowloris on Port Area",
        description="Slow-rate HTTP attack on port area. Subtler than volumetric — tests LLM nuance.",
        target_zone="port_area",
        target_zone_name="Mumbai Port",
        security_level=3,
        severity="MEDIUM",
        total_duration_sec=180,
        warmup_sec=30,
        cooldown_sec=15,
        phases=[
            AttackPhase(attack_type="slowloris", start_offset_sec=0,
                        duration_sec=135, intensity=0.6, events_per_second=5),
        ],
        ground_truth={
            "attack_type": "DDoS/Slowloris",
            "severity": "MEDIUM",
            "target_zone": "port_area",
        },
        mitre_ttps=["T0883", "T0813"],
    ),
    "S6": ScenarioConfig(
        scenario_id="S6",
        name="DNS Amplification on School Complex",
        description="DNS amplification attack exploiting open resolvers near school zone.",
        target_zone="school_complex",
        target_zone_name="IIT Bombay School Complex",
        security_level=2,
        severity="HIGH",
        total_duration_sec=120,
        warmup_sec=20,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="dns_amplification", start_offset_sec=0,
                        duration_sec=90, intensity=0.7, events_per_second=20),
        ],
        ground_truth={
            "attack_type": "DDoS/DNS Amplification",
            "severity": "HIGH",
            "target_zone": "school_complex",
        },
        mitre_ttps=["T0883", "T0813"],
    ),
    "S7": ScenarioConfig(
        scenario_id="S7",
        name="Multi-Vector DDoS on Highway Corridor",
        description="Coordinated attack combining HTTP flood + SYN flood + UDP flood on highway.",
        target_zone="highway_corridor",
        target_zone_name="Western Express Highway",
        security_level=2,
        severity="HIGH",
        total_duration_sec=180,
        warmup_sec=20,
        cooldown_sec=15,
        phases=[
            AttackPhase(attack_type="http_flood", start_offset_sec=0,
                        duration_sec=60, intensity=0.7, events_per_second=15),
            AttackPhase(attack_type="syn_flood", start_offset_sec=30,
                        duration_sec=90, intensity=0.8, events_per_second=20),
            AttackPhase(attack_type="udp_flood", start_offset_sec=60,
                        duration_sec=85, intensity=0.6, events_per_second=10),
        ],
        ground_truth={
            "attack_type": "DDoS/Multi-Vector",
            "severity": "HIGH",
            "target_zone": "highway_corridor",
        },
        mitre_ttps=["T0883", "T0804", "T0813"],
    ),
    "M1": ScenarioConfig(
        scenario_id="M1",
        name="Mirai-Like Botnet on Highway Corridor",
        description="IoT botnet recruitment via default credentials. Based on CERT-In 2025 Indian smart city botnet threats.",
        target_zone="highway_corridor",
        target_zone_name="Western Express Highway",
        security_level=2,
        severity="HIGH",
        total_duration_sec=180,
        warmup_sec=20,
        cooldown_sec=15,
        phases=[
            AttackPhase(attack_type="botnet", start_offset_sec=0,
                        duration_sec=145, intensity=0.7,
                        target_devices="all", events_per_second=8),
        ],
        ground_truth={
            "attack_type": "Malware/Botnet",
            "severity": "HIGH",
            "target_zone": "highway_corridor",
        },
        mitre_ttps=["T0882", "T0875", "T0869", "T0813"],
    ),
    "M2": ScenarioConfig(
        scenario_id="M2",
        name="Ransomware on Hospital Controllers",
        description="Ransomware targeting hospital zone controllers. Based on AIIMS Delhi 2022 ransomware attack.",
        target_zone="reliance_hospital",
        target_zone_name="Reliance Hospital",
        security_level=4,
        severity="CRITICAL",
        total_duration_sec=150,
        warmup_sec=20,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="ransomware", start_offset_sec=0,
                        duration_sec=120, intensity=0.9, events_per_second=8),
        ],
        ground_truth={
            "attack_type": "Malware/Ransomware",
            "severity": "CRITICAL",
            "target_zone": "reliance_hospital",
        },
        mitre_ttps=["T0883", "T0875", "T0834"],
    ),
    "M3": ScenarioConfig(
        scenario_id="M3",
        name="Firmware Tampering on Airport",
        description="Firmware integrity attacks on airport smart poles. Critical infrastructure (SL-4).",
        target_zone="airport",
        target_zone_name="CSM International Airport",
        security_level=4,
        severity="CRITICAL",
        total_duration_sec=120,
        warmup_sec=20,
        cooldown_sec=10,
        phases=[
            AttackPhase(attack_type="firmware_tamper", start_offset_sec=0,
                        duration_sec=90, intensity=0.8,
                        target_devices="all", events_per_second=5),
        ],
        ground_truth={
            "attack_type": "Malware/Firmware Tampering",
            "severity": "CRITICAL",
            "target_zone": "airport",
        },
        mitre_ttps=["T0883", "T0875"],
    ),
    "M4": ScenarioConfig(
        scenario_id="M4",
        name="Data Exfiltration on BKC Commercial",
        description="Slow data exfiltration from BKC zone. Based on Mumbai power grid attack (2020) intelligence gathering.",
        target_zone="bkc_commercial",
        target_zone_name="BKC Commercial",
        security_level=2,
        severity="HIGH",
        total_duration_sec=180,
        warmup_sec=30,
        cooldown_sec=15,
        phases=[
            AttackPhase(attack_type="data_exfiltration", start_offset_sec=0,
                        duration_sec=135, intensity=0.5, events_per_second=3),
        ],
        ground_truth={
            "attack_type": "Malware/Data Exfiltration",
            "severity": "HIGH",
            "target_zone": "bkc_commercial",
        },
        mitre_ttps=["T0882", "T0869"],
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Arena Controller
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvaluationRun:
    """A single evaluation run: one model × one scenario."""
    run_id: str
    model_id: str
    scenario_id: str
    start_time: str = ""
    end_time: str = ""
    events_injected: int = 0
    agent_results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed


class ArenaController:
    """
    Master controller for the AI Cyber Arena.

    Orchestrates the full evaluation pipeline:
    1. Start infrastructure (Redpanda, Redis)
    2. For each model × each scenario:
       a. Configure the model in the registry
       b. Start the target zone simulator
       c. Run the attack scenario
       d. Collect and score agent detection results
    3. Aggregate results into evaluation reports
    """

    def __init__(
        self,
        kafka_servers: str = "localhost:19092",
        redis_url: str = "redis://localhost:6379/0",
        compose_dir: str = None,
        mode: str = "local",  # "local" or "docker"
    ):
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        self.compose_dir = compose_dir or str(
            Path(__file__).parent.parent  # agent_eval/
        )
        self.mode = mode
        self.orchestrator = AttackOrchestrator(kafka_servers=kafka_servers)
        self.runs: List[EvaluationRun] = []
        self.results_dir = Path(self.compose_dir) / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Redis connection for live pipeline communication
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis_lib.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"Redis connected: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis not available: {e} — will use fallback collection")
                self.redis_client = None

    # ── Docker Management ──────────────────────────────────────────────────

    def _docker_compose(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """Run a docker compose command."""
        cmd = ["docker", "compose", *args]
        logger.info(f"Running: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=self.compose_dir,
            capture_output=True,
            text=True,
            check=check,
        )

    def start_infrastructure(self):
        """Start core infrastructure services (Redpanda, Redis)."""
        if self.mode != "docker":
            logger.info("Local mode — assuming infrastructure is already running")
            return

        logger.info("Starting core infrastructure...")
        self._docker_compose("up", "-d", "redpanda", "redis")
        time.sleep(5)

        # Create topics
        self._docker_compose("up", "topic-init")
        logger.info("Infrastructure ready")

    def start_zone(self, zone_id: str):
        """Start a specific zone simulator container."""
        if self.mode != "docker":
            logger.info(f"Local mode — zone '{zone_id}' (simulated by attack orchestrator)")
            return

        zone_cfg = ZONE_CONFIGS.get(zone_id)
        if not zone_cfg:
            logger.error(f"Unknown zone: {zone_id}")
            return

        service = zone_cfg["service_name"]
        logger.info(f"Starting zone container: {service}")
        self._docker_compose("up", "-d", service)
        time.sleep(3)

    def stop_zone(self, zone_id: str):
        """Stop a specific zone simulator container."""
        if self.mode != "docker":
            return

        zone_cfg = ZONE_CONFIGS.get(zone_id)
        if not zone_cfg:
            return

        service = zone_cfg["service_name"]
        logger.info(f"Stopping zone container: {service}")
        self._docker_compose("stop", service)

    def stop_all_zones(self):
        """Stop all zone simulator containers."""
        if self.mode != "docker":
            return

        for zone_id, cfg in ZONE_CONFIGS.items():
            self._docker_compose("stop", cfg["service_name"], check=False)

    # ── Model Management ───────────────────────────────────────────────────

    def set_model(self, model_id: str) -> Dict[str, Any]:
        """Configure the active model for evaluation. Writes to Redis so live pipeline picks it up."""
        # Push to Redis for live pipeline model swap
        if self.redis_client:
            try:
                self.redis_client.set("arena:active_model", model_id)
                logger.info(f"Model set in Redis: {model_id}")
            except Exception as e:
                logger.warning(f"Failed to set model in Redis: {e}")

        try:
            registry = ModelRegistry()
            model_cfg = registry.get_model(model_id)
            if model_cfg:
                logger.info(
                    f"Active model: {model_cfg.display_name} "
                    f"({model_cfg.parameters}) via {model_cfg.providers[0]['provider']}"
                )
                return {
                    "model_id": model_id,
                    "display_name": model_cfg.display_name,
                    "provider": model_cfg.providers[0]["provider"],
                    "context_window": model_cfg.context_window,
                }
            else:
                logger.error(f"Model not found: {model_id}")
                return {"error": f"Model not found: {model_id}"}
        except Exception as e:
            logger.warning(f"Model registry not available: {e}")
            return {"model_id": model_id, "status": "set (registry unavailable)"}

    # ── Scenario Execution ─────────────────────────────────────────────────

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        """Get a built-in or custom scenario by ID."""
        return BUILTIN_SCENARIOS.get(scenario_id)

    def list_scenarios(self) -> List[Dict[str, str]]:
        """List all available scenarios."""
        return [
            {
                "id": sid,
                "name": s.name,
                "target_zone": s.target_zone,
                "severity": s.severity,
                "duration": f"{s.total_duration_sec}s",
            }
            for sid, s in BUILTIN_SCENARIOS.items()
        ]

    def run_scenario(self, scenario_id: str, model_id: str = "llama-3.1-8b",
                     run_index: int = 1) -> EvaluationRun:
        """
        Execute a single scenario with a specific model.

        Args:
            scenario_id: Scenario ID (S1-S7, M1-M4)
            model_id: Model to evaluate
            run_index: Run number (for Pass@k evaluation)

        Returns:
            EvaluationRun with results
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        run = EvaluationRun(
            run_id=f"{scenario_id}_{model_id}_r{run_index}_{uuid.uuid4().hex[:6]}",
            model_id=model_id,
            scenario_id=scenario_id,
            start_time=datetime.now(timezone.utc).isoformat(),
            status="running",
        )
        self.runs.append(run)

        logger.info(
            f"\n{'━'*70}\n"
            f"  RUN: {run.run_id}\n"
            f"  Model: {model_id} | Scenario: {scenario.name}\n"
            f"  Run #{run_index}\n"
            f"{'━'*70}"
        )

        try:
            # 1. Set the model
            self.set_model(model_id)

            # 2. Start the target zone (Docker mode)
            self.start_zone(scenario.target_zone)

            # 3. Execute the attack scenario
            attack_result = self.orchestrator.execute_scenario(scenario, block=True)
            run.events_injected = attack_result.get("events_injected", 0)

            # 4. Collect results (placeholder — will integrate with SOC agent pipeline)
            run.agent_results = self._collect_results(scenario, run)

            # 5. Mark complete
            run.end_time = datetime.now(timezone.utc).isoformat()
            run.status = "completed"

            # 6. Stop the zone (Docker mode)
            self.stop_zone(scenario.target_zone)

        except Exception as e:
            logger.error(f"Run failed: {e}")
            run.status = "failed"
            run.agent_results["error"] = str(e)

        # Save run results
        self._save_run(run)
        return run

    def _collect_results(self, scenario: ScenarioConfig,
                         run: EvaluationRun,
                         wait_seconds: int = 45) -> Dict[str, Any]:
        """
        Collect agent detection results from Redis (written by live_pipeline.py)
        or Kafka incident_reports topic.

        In Docker mode, the live pipeline processes events in 30s windows and
        publishes results to Redis. We poll Redis until a result appears or timeout.

        In local/synthetic mode, falls back to ground truth metadata.
        """
        base_result = {
            "ground_truth": scenario.ground_truth,
            "mitre_ttps": scenario.mitre_ttps,
            "target_zone": scenario.target_zone,
            "security_level": scenario.security_level,
            "events_injected": run.events_injected,
        }

        # ── Docker mode: collect from Redis ──
        if self.mode == "docker" and self.redis_client:
            logger.info(f"Waiting up to {wait_seconds}s for pipeline results from Redis...")

            # Clear previous result before collecting new one
            try:
                self.redis_client.delete("arena:latest_result")
            except Exception:
                pass

            deadline = time.time() + wait_seconds
            while time.time() < deadline:
                try:
                    raw = self.redis_client.get("arena:latest_result")
                    if raw:
                        pipeline_result = json.loads(raw)
                        logger.info(
                            f"Pipeline result received: "
                            f"risk={pipeline_result.get('risk_level', '?')} "
                            f"events={pipeline_result.get('total_events', '?')}"
                        )
                        base_result["pipeline_result"] = pipeline_result
                        base_result["detection_pending"] = False

                        # Extract key detection fields
                        base_result["detected"] = pipeline_result.get("risk_level", "none") in ("high", "critical", "medium")
                        base_result["risk_level"] = pipeline_result.get("risk_level", "none")
                        base_result["pipeline_status"] = pipeline_result.get("pipeline_status", "unknown")
                        base_result["detection_results"] = pipeline_result.get("detection_results", {})
                        base_result["triage_result"] = pipeline_result.get("triage_result", {})
                        base_result["incident_record"] = pipeline_result.get("incident_record", {})
                        base_result["processing_time_sec"] = pipeline_result.get("processing_time_sec", 0)
                        base_result["model_id"] = pipeline_result.get("model_id", run.model_id)
                        return base_result
                except Exception as e:
                    logger.warning(f"Error reading Redis result: {e}")

                time.sleep(2)

            logger.warning("Timeout waiting for pipeline results — using fallback")
            base_result["detection_pending"] = True
            base_result["note"] = "Pipeline result not received within timeout"
            return base_result

        # ── Docker mode: fallback to Kafka consumer ──
        if self.mode == "docker" and KAFKA_AVAILABLE:
            try:
                consumer = KafkaConsumer(
                    "incident_reports",
                    bootstrap_servers=self.kafka_servers,
                    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                    auto_offset_reset="latest",
                    consumer_timeout_ms=wait_seconds * 1000,
                    group_id=f"arena_collector_{run.run_id}",
                )
                for msg in consumer:
                    if isinstance(msg.value, dict):
                        pipeline_result = msg.value
                        base_result["pipeline_result"] = pipeline_result
                        base_result["detection_pending"] = False
                        base_result["detected"] = pipeline_result.get("risk_level", "none") in ("high", "critical", "medium")
                        base_result["risk_level"] = pipeline_result.get("risk_level", "none")
                        base_result["detection_results"] = pipeline_result.get("detection_results", {})
                        base_result["processing_time_sec"] = pipeline_result.get("processing_time_sec", 0)
                        consumer.close()
                        return base_result
                consumer.close()
            except Exception as e:
                logger.warning(f"Kafka result collection failed: {e}")

        # ── Local/synthetic mode: return ground truth metadata ──
        base_result["detection_pending"] = True
        base_result["note"] = "Local mode — no live pipeline results"
        return base_result

    def _save_run(self, run: EvaluationRun):
        """Save run results to JSON file."""
        run_file = self.results_dir / f"{run.run_id}.json"
        data = {
            "run_id": run.run_id,
            "model_id": run.model_id,
            "scenario_id": run.scenario_id,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "events_injected": run.events_injected,
            "agent_results": run.agent_results,
            "metrics": run.metrics,
            "status": run.status,
        }
        with open(run_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Results saved: {run_file}")

    # ── Full Evaluation ────────────────────────────────────────────────────

    def run_full_evaluation(
        self,
        scenarios: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        runs_per_combo: int = 3,
    ) -> Dict[str, Any]:
        """
        Run a complete evaluation: all models × all scenarios × k runs.

        Args:
            scenarios: List of scenario IDs (default: all)
            models: List of model IDs (default: all from registry)
            runs_per_combo: Number of runs per model×scenario (for Pass@k)

        Returns:
            Aggregated evaluation summary.
        """
        if scenarios is None:
            scenarios = list(BUILTIN_SCENARIOS.keys())
        if models is None:
            try:
                registry = ModelRegistry()
                models = registry.list_models()
            except Exception:
                models = ["llama-3.1-8b"]

        total = len(models) * len(scenarios) * runs_per_combo
        logger.info(
            f"\n{'='*70}\n"
            f"  FULL EVALUATION\n"
            f"  Models: {len(models)} | Scenarios: {len(scenarios)} | "
            f"Runs/combo: {runs_per_combo}\n"
            f"  Total runs: {total}\n"
            f"{'='*70}"
        )

        self.start_infrastructure()
        completed = 0
        failed = 0

        for model_id in models:
            for scenario_id in scenarios:
                for k in range(1, runs_per_combo + 1):
                    try:
                        run = self.run_scenario(scenario_id, model_id, k)
                        if run.status == "completed":
                            completed += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(f"Evaluation run failed: {e}")
                        failed += 1

        self.stop_all_zones()

        summary = {
            "total_runs": total,
            "completed": completed,
            "failed": failed,
            "models": models,
            "scenarios": scenarios,
            "runs_per_combo": runs_per_combo,
            "results_dir": str(self.results_dir),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Save summary
        summary_file = self.results_dir / "evaluation_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(
            f"\n{'='*70}\n"
            f"  EVALUATION COMPLETE\n"
            f"  Completed: {completed}/{total} | Failed: {failed}\n"
            f"  Results: {self.results_dir}\n"
            f"{'='*70}"
        )

        return summary

    # ── Status & Reporting ─────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get current arena status."""
        return {
            "mode": self.mode,
            "kafka_servers": self.kafka_servers,
            "compose_dir": self.compose_dir,
            "total_runs": len(self.runs),
            "completed_runs": len([r for r in self.runs if r.status == "completed"]),
            "failed_runs": len([r for r in self.runs if r.status == "failed"]),
            "available_scenarios": list(BUILTIN_SCENARIOS.keys()),
            "results_dir": str(self.results_dir),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Cyber Arena Controller")
    parser.add_argument("--mode", choices=["local", "docker"], default="local",
                        help="Execution mode")
    parser.add_argument("--kafka", default="localhost:19092",
                        help="Kafka bootstrap servers")
    parser.add_argument("--scenario", default="S2",
                        help="Scenario ID (S1-S7, M1-M4, 'all')")
    parser.add_argument("--model", default="llama-3.1-8b",
                        help="Model to evaluate")
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of runs per model×scenario")
    parser.add_argument("--list-scenarios", action="store_true",
                        help="List available scenarios and exit")
    args = parser.parse_args()

    controller = ArenaController(
        kafka_servers=args.kafka,
        mode=args.mode,
    )

    if args.list_scenarios:
        print(f"\n{'ID':<5} {'Name':<45} {'Zone':<25} {'Severity':<10} {'Duration'}")
        print("─" * 100)
        for s in controller.list_scenarios():
            print(f"{s['id']:<5} {s['name']:<45} {s['target_zone']:<25} {s['severity']:<10} {s['duration']}")
        return

    if args.scenario == "all":
        result = controller.run_full_evaluation(
            models=[args.model],
            runs_per_combo=args.runs,
        )
    else:
        scenarios = args.scenario.split(",")
        for sid in scenarios:
            controller.run_scenario(sid.strip(), args.model)

    print(f"\nResults saved to: {controller.results_dir}")
    status = controller.get_status()
    print(f"Total runs: {status['total_runs']} | "
          f"Completed: {status['completed_runs']} | "
          f"Failed: {status['failed_runs']}")


if __name__ == "__main__":
    main()
