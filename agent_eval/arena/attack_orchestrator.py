"""
Attack Orchestrator — Scenario-driven attack injection for the AI Cyber Arena.

Reads scenario definitions (YAML or dict) and injects realistic attack traffic
into Kafka topics alongside normal zone traffic. Each attack type maps to
MITRE ATT&CK for ICS TTPs for academic defensibility.

Supported attack types:
  - http_flood      → T0883 → T0804 → T0813  (Layer 7 DDoS)
  - syn_flood       → T0883 → T0813, T0834   (Layer 4 DDoS)
  - udp_flood       → T0883 → T0813          (Volumetric DDoS)
  - slowloris       → T0883 → T0813          (Slow-rate DDoS)
  - dns_amplification → T0883 → T0813        (Amplification DDoS)
  - botnet          → T0882 → T0875 → T0869  (Mirai-like IoT botnet)
  - ransomware      → T0883 → T0875 → T0834  (File encryption + C2)
  - firmware_tamper  → T0883 → T0875         (Firmware integrity attacks)
  - data_exfiltration → T0882 → T0869       (Slow data leak)
  - multi_vector    → Combines multiple attack types simultaneously

Usage:
    orchestrator = AttackOrchestrator(kafka_servers="localhost:19092")
    orchestrator.execute_scenario(scenario_config)
"""

import os
import sys
import json
import time
import uuid
import random
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("attack-orchestrator")

# ── Try to import Kafka; fallback for testing ──
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed, attacks will be logged to stdout")

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# MITRE ATT&CK for ICS Mappings
# ═══════════════════════════════════════════════════════════════════════════════

MITRE_TTP_MAP = {
    "http_flood": {
        "technique_ids": ["T0883", "T0804", "T0813"],
        "technique_names": [
            "Internet Accessible Device",
            "Unauthorized Command Message",
            "Denial of Control",
        ],
        "tactic": "Impact",
        "description": "Layer 7 HTTP flood targeting lighting API endpoints",
    },
    "syn_flood": {
        "technique_ids": ["T0883", "T0813", "T0834"],
        "technique_names": [
            "Internet Accessible Device",
            "Denial of Control",
            "Loss of Productivity and Revenue",
        ],
        "tactic": "Impact",
        "description": "Layer 4 SYN flood exhausting connection tables",
    },
    "udp_flood": {
        "technique_ids": ["T0883", "T0813"],
        "technique_names": [
            "Internet Accessible Device",
            "Denial of Control",
        ],
        "tactic": "Impact",
        "description": "Volumetric UDP flood saturating bandwidth",
    },
    "slowloris": {
        "technique_ids": ["T0883", "T0813"],
        "technique_names": [
            "Internet Accessible Device",
            "Denial of Control",
        ],
        "tactic": "Impact",
        "description": "Slow-rate HTTP attack holding connections open",
    },
    "dns_amplification": {
        "technique_ids": ["T0883", "T0813"],
        "technique_names": [
            "Internet Accessible Device",
            "Denial of Control",
        ],
        "tactic": "Impact",
        "description": "DNS amplification via open resolvers",
    },
    "botnet": {
        "technique_ids": ["T0882", "T0875", "T0869", "T0813"],
        "technique_names": [
            "Theft of Operational Information",
            "Change Program State",
            "Standard Application Layer Protocol",
            "Denial of Control",
        ],
        "tactic": "Lateral Movement, Impact",
        "description": "Mirai-like IoT botnet recruiting via default credentials",
    },
    "ransomware": {
        "technique_ids": ["T0883", "T0875", "T0834"],
        "technique_names": [
            "Internet Accessible Device",
            "Change Program State",
            "Loss of Productivity and Revenue",
        ],
        "tactic": "Impact",
        "description": "File encryption + C2 communication on controllers",
    },
    "firmware_tamper": {
        "technique_ids": ["T0883", "T0875"],
        "technique_names": [
            "Internet Accessible Device",
            "Change Program State",
        ],
        "tactic": "Persistence",
        "description": "Firmware integrity compromise on smart poles",
    },
    "data_exfiltration": {
        "technique_ids": ["T0882", "T0869"],
        "technique_names": [
            "Theft of Operational Information",
            "Standard Application Layer Protocol",
        ],
        "tactic": "Collection, Exfiltration",
        "description": "Slow data exfiltration via covert channels",
    },
    "multi_vector": {
        "technique_ids": ["T0883", "T0804", "T0813", "T0882", "T0875"],
        "technique_names": [
            "Internet Accessible Device",
            "Unauthorized Command Message",
            "Denial of Control",
            "Theft of Operational Information",
            "Change Program State",
        ],
        "tactic": "Multiple",
        "description": "Coordinated multi-vector attack across layers",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Attack Generators
# ═══════════════════════════════════════════════════════════════════════════════

class AttackGenerators:
    """
    Static methods that produce realistic attack event dicts.
    Each generator returns events matching the format used by zone_simulator.py
    so SOC agents see a consistent schema.
    """

    # ── Common IPs used as external attacker sources ──
    EXTERNAL_BOTNET_IPS = [
        f"{random.randint(45,220)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        for _ in range(50)
    ]

    C2_SERVERS = [
        "185.220.101.42", "91.235.116.100", "45.154.98.222",
        "103.75.201.4", "194.26.135.89",
    ]

    @staticmethod
    def http_flood(zone_id: str, zone_name: str, device_id: str,
                   device_ip: str, intensity: float) -> Dict[str, Any]:
        """Layer 7 HTTP flood — massive GET/POST requests."""
        src_ip = random.choice(AttackGenerators.EXTERNAL_BOTNET_IPS)
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": src_ip,
            "source_mac": "ff:ff:ff:ff:ff:ff",
            "destination_ip": device_ip,
            "destination_port": random.choice([80, 443, 8080]),
            "protocol": "HTTP",
            "method": random.choice(["GET", "GET", "GET", "POST"]),
            "endpoint": random.choice([
                "/api/v1/lights/status", "/api/v1/lights/brightness",
                "/api/v1/sensors/ambient", "/api/v1/health",
                "/", "/api/v1/config/zone",
            ]),
            "status_code": random.choice([200, 503, 503, 429, 429, 500]),
            "response_time_ms": round(random.uniform(500, 5000) * intensity, 1),
            "bytes_sent": random.randint(50, 500),
            "bytes_received": random.randint(0, 200),
            "packet_size": random.randint(64, 1500),
            "user_agent": random.choice([
                "Mozilla/5.0", "python-requests/2.31", "curl/7.88",
                "Go-http-client/1.1", "",
            ]),
            "device_id": device_id,
            "requests_per_second": int(500 * intensity + random.randint(0, 200)),
            "suspicious": True,
            "attack_indicators": {
                "type": "http_flood",
                "rps_spike": True,
                "distributed_sources": True,
            },
        }

    @staticmethod
    def syn_flood(zone_id: str, zone_name: str, device_id: str,
                  device_ip: str, intensity: float) -> Dict[str, Any]:
        """Layer 4 SYN flood — half-open connections."""
        src_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": src_ip,
            "destination_ip": device_ip,
            "destination_port": random.choice([80, 443, 1883, 5683, 8080]),
            "protocol": "TCP",
            "method": "SYN",
            "status_code": 0,
            "response_time_ms": 0,
            "bytes_sent": 64,
            "bytes_received": 0,
            "packet_size": 64,
            "device_id": device_id,
            "connection_state": "SYN_SENT",
            "half_open_connections": int(10000 * intensity + random.randint(0, 2000)),
            "suspicious": True,
            "attack_indicators": {
                "type": "syn_flood",
                "spoofed_sources": True,
                "no_ack": True,
            },
        }

    @staticmethod
    def udp_flood(zone_id: str, zone_name: str, device_id: str,
                  device_ip: str, intensity: float) -> Dict[str, Any]:
        """Volumetric UDP flood."""
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "destination_ip": device_ip,
            "destination_port": random.choice([53, 123, 161, 5683]),
            "protocol": "UDP",
            "method": "DATAGRAM",
            "bytes_sent": random.randint(512, 4096),
            "bytes_received": 0,
            "packet_size": random.randint(512, 4096),
            "device_id": device_id,
            "packets_per_second": int(50000 * intensity),
            "bandwidth_mbps": round(100 * intensity + random.uniform(0, 50), 1),
            "suspicious": True,
            "attack_indicators": {
                "type": "udp_flood",
                "volumetric": True,
            },
        }

    @staticmethod
    def slowloris(zone_id: str, zone_name: str, device_id: str,
                  device_ip: str, intensity: float) -> Dict[str, Any]:
        """Slowloris — partial HTTP headers keeping connections alive."""
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": random.choice(AttackGenerators.EXTERNAL_BOTNET_IPS),
            "destination_ip": device_ip,
            "destination_port": 80,
            "protocol": "HTTP",
            "method": "GET",
            "endpoint": "/api/v1/lights/status",
            "status_code": 0,
            "response_time_ms": round(random.uniform(10000, 60000), 1),
            "bytes_sent": random.randint(10, 50),
            "bytes_received": 0,
            "packet_size": random.randint(40, 100),
            "device_id": device_id,
            "connection_duration_sec": round(random.uniform(30, 300), 1),
            "open_connections": int(500 * intensity + random.randint(0, 100)),
            "headers_complete": False,
            "suspicious": True,
            "attack_indicators": {
                "type": "slowloris",
                "slow_rate": True,
                "connection_exhaustion": True,
            },
        }

    @staticmethod
    def dns_amplification(zone_id: str, zone_name: str, device_id: str,
                          device_ip: str, intensity: float) -> Dict[str, Any]:
        """DNS amplification using spoofed source IP."""
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": device_ip,  # Spoofed — victim IP as source
            "destination_ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "destination_port": 53,
            "protocol": "UDP",
            "method": "DNS_QUERY",
            "query_type": "ANY",
            "bytes_sent": 64,
            "bytes_received": random.randint(2000, 4096),
            "amplification_factor": round(random.uniform(30, 70), 1),
            "packet_size": random.randint(2000, 4096),
            "device_id": device_id,
            "suspicious": True,
            "attack_indicators": {
                "type": "dns_amplification",
                "spoofed_source": True,
                "amplification": True,
            },
        }

    @staticmethod
    def botnet_recruitment(zone_id: str, zone_name: str, device_id: str,
                           device_ip: str, intensity: float,
                           stage: str = "scanning") -> Dict[str, Any]:
        """Mirai-like botnet — scan → exploit → install → C2 beacon."""
        if stage == "scanning":
            return {
                "event_type": "network_traffic",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "source_ip": random.choice(AttackGenerators.EXTERNAL_BOTNET_IPS),
                "destination_ip": device_ip,
                "destination_port": random.choice([23, 2323, 80, 8080, 161]),
                "protocol": "TCP",
                "method": "CONNECT",
                "connection_status": "established",
                "scan_type": "credential_brute_force",
                "credentials_tried": random.choice([
                    "admin:admin", "root:root", "admin:1234",
                    "root:password", "admin:default",
                ]),
                "device_id": device_id,
                "suspicious": True,
                "attack_indicators": {
                    "type": "botnet",
                    "stage": "scanning",
                    "mitre_ttp": "T0882",
                },
            }
        elif stage == "exploit":
            return {
                "event_type": "device_event",
                "event_subtype": "unauthorized_access",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "device_id": device_id,
                "device_type": "smart_pole",
                "ip_address": device_ip,
                "status": "compromised",
                "details": {
                    "access_method": "default_credentials",
                    "protocol": "telnet",
                    "privilege_level": "root",
                },
                "suspicious": True,
                "attack_indicators": {
                    "type": "botnet",
                    "stage": "exploit",
                    "mitre_ttp": "T0875",
                },
            }
        else:  # c2_beacon
            return {
                "event_type": "network_traffic",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "source_ip": device_ip,
                "destination_ip": random.choice(AttackGenerators.C2_SERVERS),
                "destination_port": random.choice([443, 8443, 4444, 31337]),
                "protocol": "HTTPS",
                "method": "POST",
                "endpoint": "/api/beacon",
                "bytes_sent": random.randint(100, 500),
                "bytes_received": random.randint(50, 200),
                "packet_size": random.randint(200, 800),
                "device_id": device_id,
                "connection_interval_sec": random.choice([30, 60, 120, 300]),
                "suspicious": True,
                "attack_indicators": {
                    "type": "botnet",
                    "stage": "c2_beacon",
                    "mitre_ttp": "T0869",
                },
            }

    @staticmethod
    def ransomware(zone_id: str, zone_name: str, device_id: str,
                   device_ip: str, intensity: float,
                   stage: str = "encryption") -> Dict[str, Any]:
        """Ransomware — encryption, C2 communication, ransom note."""
        if stage == "encryption":
            return {
                "event_type": "device_event",
                "event_subtype": "file_system_change",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "device_id": device_id,
                "device_type": "zone_controller",
                "ip_address": device_ip,
                "status": "compromised",
                "details": {
                    "files_modified": random.randint(50, 500),
                    "extensions_changed": random.sample(
                        [".enc", ".locked", ".crypto", ".crypt", ".rans"], 2
                    ),
                    "encryption_rate_files_per_sec": round(
                        random.uniform(50, 200) * intensity, 1
                    ),
                    "process_name": "svchost_update.exe",
                    "cpu_usage_pct": random.randint(85, 100),
                },
                "suspicious": True,
                "attack_indicators": {
                    "type": "ransomware",
                    "stage": "encryption",
                    "mitre_ttp": "T0875",
                },
            }
        elif stage == "c2":
            return {
                "event_type": "network_traffic",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "source_ip": device_ip,
                "destination_ip": random.choice(AttackGenerators.C2_SERVERS),
                "destination_port": 443,
                "protocol": "HTTPS",
                "method": "POST",
                "endpoint": "/report",
                "bytes_sent": random.randint(200, 1000),
                "bytes_received": random.randint(100, 500),
                "device_id": device_id,
                "suspicious": True,
                "attack_indicators": {
                    "type": "ransomware",
                    "stage": "c2_communication",
                    "mitre_ttp": "T0883",
                },
            }
        else:  # ransom_note
            return {
                "event_type": "device_event",
                "event_subtype": "ransom_note_created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zone_id": zone_id,
                "zone_name": zone_name,
                "device_id": device_id,
                "device_type": "zone_controller",
                "ip_address": device_ip,
                "status": "compromised",
                "details": {
                    "filename": "README_DECRYPT.txt",
                    "ransom_btc": round(random.uniform(0.5, 5.0), 2),
                    "deadline_hours": random.choice([24, 48, 72]),
                },
                "suspicious": True,
                "attack_indicators": {
                    "type": "ransomware",
                    "stage": "ransom_note",
                    "mitre_ttp": "T0834",
                },
            }

    @staticmethod
    def firmware_tamper(zone_id: str, zone_name: str, device_id: str,
                        device_ip: str, intensity: float) -> Dict[str, Any]:
        """Firmware tampering — integrity check failures."""
        return {
            "event_type": "device_event",
            "event_subtype": "firmware_check",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "device_id": device_id,
            "device_type": "smart_pole",
            "ip_address": device_ip,
            "firmware_version": "2.1.4",
            "status": "compromised",
            "details": {
                "integrity_check": "FAILED",
                "checksum_expected": "a3b2c1d4e5f6",
                "checksum_actual": f"tampered_{uuid.uuid4().hex[:8]}",
                "tampered_sections": random.sample(
                    ["bootloader", "kernel", "config", "certificates"], 2
                ),
            },
            "suspicious": True,
            "attack_indicators": {
                "type": "firmware_tamper",
                "mitre_ttp": "T0875",
            },
        }

    @staticmethod
    def data_exfiltration(zone_id: str, zone_name: str, device_id: str,
                          device_ip: str, intensity: float) -> Dict[str, Any]:
        """Slow data exfiltration via DNS tunneling or HTTPS."""
        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id,
            "zone_name": zone_name,
            "source_ip": device_ip,
            "destination_ip": random.choice(AttackGenerators.C2_SERVERS),
            "destination_port": random.choice([53, 443]),
            "protocol": random.choice(["DNS", "HTTPS"]),
            "method": "POST" if random.random() > 0.5 else "DNS_QUERY",
            "bytes_sent": random.randint(500, 5000),
            "bytes_received": random.randint(50, 200),
            "device_id": device_id,
            "exfiltration_data": {
                "data_type": random.choice([
                    "zone_topology", "credential_store", "sensor_readings",
                    "firmware_config", "network_map",
                ]),
                "estimated_bytes": random.randint(10000, 500000),
            },
            "suspicious": True,
            "attack_indicators": {
                "type": "data_exfiltration",
                "covert_channel": True,
                "mitre_ttp": "T0882",
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Attack Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AttackPhase:
    """A single phase within an attack scenario."""
    attack_type: str
    start_offset_sec: float  # Seconds after scenario start
    duration_sec: float
    intensity: float  # 0.0 to 1.0
    target_devices: str = "random"  # "random", "all", or specific device_id
    events_per_second: float = 10.0
    zone_override: str = ""  # Override target zone for multi-zone scenarios


@dataclass
class ScenarioConfig:
    """Complete scenario definition."""
    scenario_id: str
    name: str
    description: str
    target_zone: str
    target_zone_name: str
    security_level: int
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    total_duration_sec: float
    warmup_sec: float = 30.0  # Normal traffic before attack starts
    cooldown_sec: float = 10.0  # Normal traffic after attack ends
    phases: List[AttackPhase] = field(default_factory=list)
    ground_truth: Dict[str, Any] = field(default_factory=dict)
    mitre_ttps: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioConfig":
        """Create ScenarioConfig from a dictionary (e.g., parsed YAML)."""
        phases = [
            AttackPhase(**p) for p in data.get("phases", [])
        ]
        return cls(
            scenario_id=data["scenario_id"],
            name=data["name"],
            description=data.get("description", ""),
            target_zone=data["target_zone"],
            target_zone_name=data.get("target_zone_name", data["target_zone"]),
            security_level=data.get("security_level", 2),
            severity=data.get("severity", "HIGH"),
            total_duration_sec=data.get("total_duration_sec", 120),
            warmup_sec=data.get("warmup_sec", 30),
            cooldown_sec=data.get("cooldown_sec", 10),
            phases=phases,
            ground_truth=data.get("ground_truth", {}),
            mitre_ttps=data.get("mitre_ttps", []),
        )

    @classmethod
    def from_yaml(cls, path: str) -> "ScenarioConfig":
        """Load scenario from a YAML file."""
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required to load scenario YAML files")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class AttackOrchestrator:
    """
    Injects scenario-driven attack traffic into Kafka topics.

    The orchestrator generates attack events that match the zone_simulator's
    event schema, so SOC agents see a consistent data format. It supports
    multi-phase attacks where different attack types activate at different
    times during a scenario.
    """

    def __init__(self, kafka_servers: str = "localhost:19092"):
        self.kafka_servers = kafka_servers
        self.producer: Optional[Any] = None
        self.running = False
        self._lock = threading.Lock()
        self.attack_log: List[Dict[str, Any]] = []

        # Zone device registry (device_id → device info)
        # Populated when a scenario targets a zone
        self._zone_devices: Dict[str, Dict[str, Any]] = {}

    def _connect_kafka(self):
        """Connect to Kafka/Redpanda broker."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available, attack events logged to stdout only")
            return

        for attempt in range(10):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.kafka_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                    acks="all",
                    retries=3,
                )
                logger.info(f"Connected to Kafka at {self.kafka_servers}")
                return
            except Exception as e:
                logger.warning(f"Kafka connection attempt {attempt+1}/10 failed: {e}")
                time.sleep(2)

        logger.error("Failed to connect to Kafka after 10 attempts")

    def _publish(self, topic: str, event: Dict[str, Any]):
        """Publish attack event to Kafka or stdout."""
        if self.producer:
            try:
                self.producer.send(topic, value=event)
            except Exception as e:
                logger.error(f"Failed to publish to {topic}: {e}")
        else:
            logger.info(f"[ATTACK][{topic}] {json.dumps(event, default=str)[:300]}")

    def _generate_zone_devices(self, zone_id: str, zone_name: str,
                                num_devices: int = 10) -> List[Dict[str, str]]:
        """Generate synthetic device info for a target zone."""
        devices = []
        for i in range(num_devices):
            dev = {
                "device_id": f"{zone_id}_pole_{i:03d}",
                "zone_id": zone_id,
                "zone_name": zone_name,
                "ip_address": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                "mac_address": ":".join(f"{random.randint(0,255):02x}" for _ in range(6)),
                "firmware_version": "2.1.4",
            }
            devices.append(dev)
            self._zone_devices[dev["device_id"]] = dev
        return devices

    def _select_targets(self, devices: List[Dict], phase: AttackPhase) -> List[Dict]:
        """Select target devices for an attack phase."""
        if phase.target_devices == "all":
            return devices
        elif phase.target_devices == "random":
            count = max(1, len(devices) // 3)
            return random.sample(devices, min(count, len(devices)))
        else:
            # Specific device_id
            return [d for d in devices if d["device_id"] == phase.target_devices]

    def _generate_attack_event(self, attack_type: str, zone_id: str,
                                zone_name: str, device: Dict,
                                intensity: float, phase_progress: float) -> Dict[str, Any]:
        """Generate a single attack event based on type."""
        dev_id = device["device_id"]
        dev_ip = device["ip_address"]

        generators = {
            "http_flood": lambda: AttackGenerators.http_flood(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "syn_flood": lambda: AttackGenerators.syn_flood(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "udp_flood": lambda: AttackGenerators.udp_flood(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "slowloris": lambda: AttackGenerators.slowloris(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "dns_amplification": lambda: AttackGenerators.dns_amplification(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "firmware_tamper": lambda: AttackGenerators.firmware_tamper(
                zone_id, zone_name, dev_id, dev_ip, intensity),
            "data_exfiltration": lambda: AttackGenerators.data_exfiltration(
                zone_id, zone_name, dev_id, dev_ip, intensity),
        }

        # Multi-stage attacks
        if attack_type == "botnet":
            if phase_progress < 0.3:
                stage = "scanning"
            elif phase_progress < 0.6:
                stage = "exploit"
            else:
                stage = "c2_beacon"
            return AttackGenerators.botnet_recruitment(
                zone_id, zone_name, dev_id, dev_ip, intensity, stage)

        elif attack_type == "ransomware":
            if phase_progress < 0.6:
                stage = "encryption"
            elif phase_progress < 0.85:
                stage = "c2"
            else:
                stage = "ransom_note"
            return AttackGenerators.ransomware(
                zone_id, zone_name, dev_id, dev_ip, intensity, stage)

        elif attack_type == "multi_vector":
            # Pick from multiple attack types
            sub_type = random.choice(["http_flood", "syn_flood", "udp_flood", "botnet"])
            return self._generate_attack_event(
                sub_type, zone_id, zone_name, device, intensity, phase_progress)

        # Simple attack types
        gen = generators.get(attack_type)
        if gen:
            return gen()

        logger.warning(f"Unknown attack type: {attack_type}")
        return AttackGenerators.http_flood(zone_id, zone_name, dev_id, dev_ip, intensity)

    def execute_scenario(self, scenario: ScenarioConfig,
                         block: bool = True) -> Dict[str, Any]:
        """
        Execute a complete attack scenario.

        Args:
            scenario: The scenario configuration to execute.
            block: If True, blocks until scenario completes.
                   If False, runs in a background thread.

        Returns:
            Execution summary with event counts and timing.
        """
        self._connect_kafka()
        self.running = True

        logger.info(
            f"{'='*60}\n"
            f"  SCENARIO: {scenario.name} ({scenario.scenario_id})\n"
            f"  Target: {scenario.target_zone_name} (SL-{scenario.security_level})\n"
            f"  Severity: {scenario.severity}\n"
            f"  Duration: {scenario.total_duration_sec}s "
            f"(warmup={scenario.warmup_sec}s, cooldown={scenario.cooldown_sec}s)\n"
            f"  Phases: {len(scenario.phases)}\n"
            f"{'='*60}"
        )

        # Generate target devices for each zone used in the scenario
        zone_devices_map: Dict[str, List[Dict]] = {}
        # Main zone
        zone_devices_map[scenario.target_zone] = self._generate_zone_devices(
            scenario.target_zone, scenario.target_zone_name, num_devices=10,
        )
        # Per-phase zone overrides
        zone_names = {
            "bkc_commercial": "BKC Commercial",
            "hospital_zone": "Reliance Hospital",
            "airport_zone": "Mumbai Airport",
            "port_zone": "Mumbai Port Trust",
            "school_zone": "School Zone",
            "residential_zone": "Residential Area",
            "highway_corridor": "Western Express Highway",
        }
        for phase in scenario.phases:
            zid = phase.zone_override
            if zid and zid not in zone_devices_map:
                zname = zone_names.get(zid, zid)
                zone_devices_map[zid] = self._generate_zone_devices(
                    zid, zname, num_devices=10,
                )
        # Default devices for backward compatibility
        devices = zone_devices_map[scenario.target_zone]

        result = {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "events_injected": 0,
            "events_by_type": {},
            "phases_executed": 0,
        }

        if block:
            self._run_scenario_loop(scenario, devices, result)
        else:
            thread = threading.Thread(
                target=self._run_scenario_loop,
                args=(scenario, devices, result),
                daemon=True,
            )
            thread.start()

        return result

    def _run_scenario_loop(self, scenario: ScenarioConfig,
                           devices: List[Dict], result: Dict[str, Any]):
        """Main scenario execution loop."""
        start_time = time.time()
        total_duration = scenario.total_duration_sec
        events_injected = 0
        events_by_type: Dict[str, int] = {}

        # Publish scenario-start alert
        start_alert = {
            "event_type": "scenario_marker",
            "marker_type": "scenario_start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.name,
            "target_zone": scenario.target_zone,
            "severity": scenario.severity,
            "ground_truth": scenario.ground_truth,
            "mitre_ttps": scenario.mitre_ttps,
        }
        self._publish("cyber_alerts", start_alert)

        while self.running and (time.time() - start_time) < total_duration:
            elapsed = time.time() - start_time

            # Determine which phases are active
            active_phases = []
            for phase in scenario.phases:
                phase_start = scenario.warmup_sec + phase.start_offset_sec
                phase_end = phase_start + phase.duration_sec
                if phase_start <= elapsed < phase_end:
                    progress = (elapsed - phase_start) / phase.duration_sec
                    active_phases.append((phase, progress))

            if not active_phases:
                # Warmup or cooldown period — no attacks
                time.sleep(0.1)
                continue

            # Generate attack events for each active phase
            for phase, progress in active_phases:
                # Use per-phase zone override if specified
                phase_zone = phase.zone_override or scenario.target_zone
                phase_zone_name = zone_names.get(phase_zone, phase_zone)
                phase_devices = zone_devices_map.get(phase_zone, devices)
                targets = self._select_targets(phase_devices, phase)
                events_this_tick = max(1, int(phase.events_per_second / 10))

                for _ in range(events_this_tick):
                    device = random.choice(targets)
                    event = self._generate_attack_event(
                        phase.attack_type,
                        phase_zone,
                        phase_zone_name,
                        device,
                        phase.intensity,
                        progress,
                    )

                    # Determine Kafka topic based on event type
                    event_type = event.get("event_type", "")
                    if event_type == "network_traffic":
                        topic = "network_events"
                    elif event_type in ("device_event", "process_execution",
                                        "file_system_change", "firmware_check"):
                        topic = "device_events"
                    else:
                        topic = "cyber_alerts"

                    self._publish(topic, event)
                    events_injected += 1

                    atk = phase.attack_type
                    events_by_type[atk] = events_by_type.get(atk, 0) + 1

            # ~100ms tick
            time.sleep(0.1)

        # Publish scenario-end marker
        end_alert = {
            "event_type": "scenario_marker",
            "marker_type": "scenario_end",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.name,
            "events_injected": events_injected,
            "duration_actual_sec": round(time.time() - start_time, 2),
        }
        self._publish("cyber_alerts", end_alert)

        if self.producer:
            self.producer.flush()

        # Update result
        result["end_time"] = datetime.now(timezone.utc).isoformat()
        result["events_injected"] = events_injected
        result["events_by_type"] = events_by_type
        result["phases_executed"] = len(scenario.phases)
        result["duration_actual_sec"] = round(time.time() - start_time, 2)

        self.attack_log.append(result)

        logger.info(
            f"Scenario '{scenario.name}' completed: "
            f"{events_injected} events injected in {result['duration_actual_sec']}s"
        )

        self.running = False

    def stop(self):
        """Stop the current scenario execution."""
        self.running = False
        if self.producer:
            self.producer.flush()
            self.producer.close()
            self.producer = None

    def get_attack_log(self) -> List[Dict[str, Any]]:
        """Return the log of all executed scenarios."""
        return self.attack_log

    @staticmethod
    def get_mitre_mapping(attack_type: str) -> Dict[str, Any]:
        """Get MITRE ATT&CK mapping for an attack type."""
        return MITRE_TTP_MAP.get(attack_type, {
            "technique_ids": [],
            "technique_names": [],
            "tactic": "Unknown",
            "description": f"Unknown attack type: {attack_type}",
        })


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for standalone testing
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run a quick demo scenario to verify the orchestrator works."""
    import argparse

    parser = argparse.ArgumentParser(description="Attack Orchestrator — inject attack traffic")
    parser.add_argument("--kafka", default="localhost:19092", help="Kafka bootstrap servers")
    parser.add_argument("--scenario", default="demo", help="Scenario to run (demo | yaml path)")
    parser.add_argument("--duration", type=int, default=60, help="Total scenario duration (sec)")
    parser.add_argument("--intensity", type=float, default=0.8, help="Attack intensity (0-1)")
    args = parser.parse_args()

    if args.scenario == "demo":
        # Built-in demo: HTTP flood on BKC Commercial
        scenario = ScenarioConfig(
            scenario_id="S2-demo",
            name="HTTP Flood on BKC Commercial (Demo)",
            description="Demo scenario: Layer 7 HTTP flood targeting BKC lighting API",
            target_zone="bkc_commercial",
            target_zone_name="BKC Commercial",
            security_level=2,
            severity="HIGH",
            total_duration_sec=args.duration,
            warmup_sec=10,
            cooldown_sec=5,
            phases=[
                AttackPhase(
                    attack_type="http_flood",
                    start_offset_sec=0,
                    duration_sec=args.duration - 15,
                    intensity=args.intensity,
                    target_devices="random",
                    events_per_second=20,
                ),
            ],
            ground_truth={
                "attack_type": "DDoS/HTTP Flood",
                "severity": "HIGH",
                "target_zone": "bkc_commercial",
            },
            mitre_ttps=["T0883", "T0804", "T0813"],
        )
    else:
        scenario = ScenarioConfig.from_yaml(args.scenario)

    orchestrator = AttackOrchestrator(kafka_servers=args.kafka)
    try:
        result = orchestrator.execute_scenario(scenario, block=True)
        print(f"\n{'='*60}")
        print(f"  Scenario Complete")
        print(f"  Events injected: {result['events_injected']}")
        print(f"  By type: {result['events_by_type']}")
        print(f"  Duration: {result.get('duration_actual_sec', '?')}s")
        print(f"{'='*60}")
    except KeyboardInterrupt:
        orchestrator.stop()
        print("\nStopped.")


if __name__ == "__main__":
    main()
