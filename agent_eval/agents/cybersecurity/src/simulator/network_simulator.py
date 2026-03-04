# backend/cybersecurity/src/simulator/network_simulator.py

"""
Network Simulator for the Smart Lighting Grid — Mumbai Metropolitan Area.

Generates realistic network traffic events for 7 zones, publishes to Kafka,
and supports manual attack triggers (DDoS, Malware, Firmware Tampering, Recon).

Data flow: Simulator → Kafka → Consumer → Agent → WebSocket → Dashboard
"""

import json
import logging
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# Mumbai Zone Definitions
# ═════════════════════════════════════════════════════════════════════════════

MUMBAI_ZONES = [
    {
        "id": "SL-ZONE-A",
        "name": "Airport Zone",
        "area": "CSM International Airport",
        "type": "airport",
        "center": [19.0896, 72.8656],
        "bounds": [[19.0856, 72.8606], [19.0936, 72.8706]],
        "device_count": 10,
        "priority": "critical",
        "color": "#ef4444",
    },
    {
        "id": "SL-ZONE-B",
        "name": "Port Zone",
        "area": "Mumbai Port Trust",
        "type": "port",
        "center": [18.9388, 72.8354],
        "bounds": [[18.9348, 72.8304], [18.9428, 72.8404]],
        "device_count": 8,
        "priority": "high",
        "color": "#f97316",
    },
    {
        "id": "SL-ZONE-C",
        "name": "Industrial Zone",
        "area": "MIDC Andheri East",
        "type": "industrial",
        "center": [19.1136, 72.8697],
        "bounds": [[19.1096, 72.8647], [19.1176, 72.8747]],
        "device_count": 8,
        "priority": "high",
        "color": "#eab308",
    },
    {
        "id": "SL-ZONE-D",
        "name": "Residential Zone",
        "area": "Bandra-Juhu",
        "type": "residential",
        "center": [19.0596, 72.8295],
        "bounds": [[19.0556, 72.8245], [19.0636, 72.8345]],
        "device_count": 10,
        "priority": "medium",
        "color": "#22c55e",
    },
    {
        "id": "SL-ZONE-E",
        "name": "Hospital Zone",
        "area": "Hinduja / Lilavati Hospital",
        "type": "hospital",
        "center": [19.0509, 72.8294],
        "bounds": [[19.0479, 72.8254], [19.0539, 72.8334]],
        "device_count": 6,
        "priority": "critical",
        "color": "#06b6d4",
    },
    {
        "id": "SL-ZONE-F",
        "name": "Commercial Zone",
        "area": "BKC / Nariman Point",
        "type": "commercial",
        "center": [19.0652, 72.8697],
        "bounds": [[19.0612, 72.8647], [19.0692, 72.8747]],
        "device_count": 10,
        "priority": "high",
        "color": "#8b5cf6",
    },
    {
        "id": "SL-ZONE-G",
        "name": "Transport Hub",
        "area": "CSMT / Dadar",
        "type": "transport",
        "center": [18.9398, 72.8355],
        "bounds": [[18.9358, 72.8305], [18.9438, 72.8405]],
        "device_count": 8,
        "priority": "high",
        "color": "#ec4899",
    },
]


def _generate_devices(zones: list) -> Dict[str, Dict[str, Any]]:
    """Generate smart light pole devices for each zone."""
    devices = {}
    for zone in zones:
        for i in range(1, zone["device_count"] + 1):
            device_id = f"{zone['id']}-{i:03d}"
            # Scatter device within zone bounds
            lat = random.uniform(zone["bounds"][0][0], zone["bounds"][1][0])
            lng = random.uniform(zone["bounds"][0][1], zone["bounds"][1][1])
            devices[device_id] = {
                "device_id": device_id,
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "zone_type": zone["type"],
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "status": "online",
                "brightness": random.randint(60, 100),
                "firmware_version": "3.2.1",
                "last_heartbeat": datetime.now().isoformat(),
            }
    return devices


# ═════════════════════════════════════════════════════════════════════════════
# Network Simulator
# ═════════════════════════════════════════════════════════════════════════════

class NetworkSimulator:
    """
    Generates realistic smart-lighting grid events and publishes to Kafka.
    Supports normal traffic + manual attack triggers.
    """

    def __init__(self):
        self.zones = MUMBAI_ZONES
        self.devices = _generate_devices(self.zones)
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._producer = None

        # Counters
        self.events_generated = 0
        self.start_time: Optional[datetime] = None
        self.active_attacks: List[Dict[str, Any]] = []
        self._attack_lock = threading.Lock()

        # Recent events buffer for WebSocket catch-up
        self.recent_events: deque = deque(maxlen=200)

        # Custom zones added via admin dashboard
        self.custom_zones: List[Dict[str, Any]] = []

    # ── Producer ──

    def _get_producer(self):
        """Lazy-init Kafka producer (avoids import-time errors)."""
        if self._producer is None:
            try:
                from kafka import KafkaProducer
                from ..config.settings import config
                self._producer = KafkaProducer(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda x: json.dumps(x, default=str).encode("utf-8"),
                    key_serializer=lambda x: x.encode("utf-8") if x else None,
                )
                logger.info("Simulator Kafka producer initialized")
            except Exception as e:
                logger.warning(f"Kafka producer init failed (simulator will buffer only): {e}")
        return self._producer

    def _publish(self, topic: str, key: str, event: Dict[str, Any]):
        """Publish an event to Kafka and buffer it."""
        self.recent_events.append(event)
        self.events_generated += 1
        producer = self._get_producer()
        if producer:
            try:
                producer.send(topic, key=key, value=event)
            except Exception as e:
                logger.debug(f"Kafka send failed: {e}")

    # ── Lifecycle ──

    def start(self):
        if self.is_running:
            return {"status": "already_running"}
        self.is_running = True
        self.start_time = datetime.now()
        self.events_generated = 0
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Network simulator started")
        return {"status": "started"}

    def stop(self):
        if not self.is_running:
            return {"status": "already_stopped"}
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Network simulator stopped")
        return {"status": "stopped"}

    def get_status(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        return {
            "is_running": self.is_running,
            "uptime_seconds": round(uptime, 1),
            "events_generated": self.events_generated,
            "events_per_second": round(self.events_generated / max(uptime, 1), 2),
            "active_attacks": [
                {"type": a["type"], "zone": a["zone"], "remaining_seconds": max(0, a["end_time"] - time.time())}
                for a in self.active_attacks
            ],
            "zone_count": len(self.zones) + len(self.custom_zones),
            "device_count": len(self.devices),
        }

    def get_zones(self) -> List[Dict[str, Any]]:
        """Return all zone definitions (built-in + custom)."""
        all_zones = self.zones + self.custom_zones
        result = []
        for z in all_zones:
            zone_devices = [d for d in self.devices.values() if d["zone_id"] == z["id"]]
            result.append({
                **z,
                "devices": zone_devices,
                "device_count": len(zone_devices),
            })
        return result

    def add_zone(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new zone from the admin dashboard."""
        zone_id = zone_data.get("id", f"SL-ZONE-CUSTOM-{len(self.custom_zones) + 1}")
        new_zone = {
            "id": zone_id,
            "name": zone_data.get("name", f"Custom Zone {len(self.custom_zones) + 1}"),
            "area": zone_data.get("area", "Custom Area"),
            "type": zone_data.get("type", "custom"),
            "center": zone_data.get("center", [19.076, 72.877]),
            "bounds": zone_data.get("bounds", [[19.073, 72.874], [19.079, 72.880]]),
            "device_count": zone_data.get("device_count", 5),
            "priority": zone_data.get("priority", "medium"),
            "color": zone_data.get("color", "#6b7280"),
        }
        self.custom_zones.append(new_zone)
        # Generate devices for the new zone
        new_devices = _generate_devices([new_zone])
        self.devices.update(new_devices)
        logger.info(f"Added custom zone: {zone_id} with {len(new_devices)} devices")
        return {"zone": new_zone, "devices_created": len(new_devices)}

    # ── Main Loop ──

    def _run_loop(self):
        """Main event generation loop."""
        logger.info("Simulator loop started")
        while self.is_running:
            try:
                # Generate normal traffic events
                self._generate_normal_traffic()

                # Process active attacks
                with self._attack_lock:
                    now = time.time()
                    still_active = []
                    for attack in self.active_attacks:
                        if now < attack["end_time"]:
                            self._generate_attack_traffic(attack)
                            still_active.append(attack)
                        else:
                            logger.info(f"Attack ended: {attack['type']} on {attack['zone']}")
                    self.active_attacks = still_active

                time.sleep(random.uniform(1.0, 2.5))

            except Exception as e:
                logger.error(f"Simulator loop error: {e}")
                time.sleep(2)

    # ── Normal Traffic ──

    def _generate_normal_traffic(self):
        """Generate routine smart lighting grid events."""
        now = datetime.now()

        # Pick a random subset of devices for this tick
        device_list = list(self.devices.values())
        active_devices = random.sample(device_list, min(len(device_list), random.randint(3, 8)))

        for device in active_devices:
            event_type = random.choice([
                "heartbeat", "light_status", "sensor_reading",
                "network_traffic", "connection_attempt",
            ])

            if event_type == "heartbeat":
                event = self._make_heartbeat(device, now)
                self._publish("device_events", device["device_id"], event)

            elif event_type == "light_status":
                event = self._make_light_status(device, now)
                self._publish("device_events", device["device_id"], event)

            elif event_type == "sensor_reading":
                event = self._make_sensor_reading(device, now)
                self._publish("device_events", device["device_id"], event)

            elif event_type == "network_traffic":
                event = self._make_network_traffic(device, now, is_attack=False)
                self._publish("network_events", device["device_id"], event)

            elif event_type == "connection_attempt":
                event = self._make_connection_attempt(device, now, is_suspicious=False)
                self._publish("network_events", device["device_id"], event)

    def _make_heartbeat(self, device: dict, now: datetime) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "heartbeat",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "status": "online",
            "uptime_hours": random.randint(24, 8760),
            "firmware_version": device["firmware_version"],
            "cpu_usage": random.randint(5, 35),
            "memory_usage": random.randint(20, 50),
            "severity": "low",
        }

    def _make_light_status(self, device: dict, now: datetime) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "light_status",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "brightness": random.randint(40, 100),
            "power_consumption_w": round(random.uniform(50, 150), 1),
            "temperature_c": round(random.uniform(25, 45), 1),
            "operational_hours": random.randint(100, 50000),
            "severity": "low",
        }

    def _make_sensor_reading(self, device: dict, now: datetime) -> dict:
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "sensor_reading",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "ambient_light_lux": random.randint(0, 800),
            "motion_detected": random.random() < 0.3,
            "temperature_c": round(random.uniform(22, 38), 1),
            "humidity_pct": random.randint(40, 90),
            "air_quality_aqi": random.randint(30, 200),
            "severity": "low",
        }

    def _make_network_traffic(self, device: dict, now: datetime, is_attack: bool = False) -> dict:
        if is_attack:
            rps = random.randint(2000, 10000)
            source_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            severity = "critical" if rps > 5000 else "high"
        else:
            rps = random.randint(10, 200)
            source_ip = f"10.{device['zone_id'][-1]}.{random.randint(1,10)}.{random.randint(1,254)}"
            severity = "low"

        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "network_traffic",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "source_ip": source_ip,
            "destination_ip": f"10.0.{random.randint(1,10)}.{random.randint(1,254)}",
            "protocol": random.choice(["TCP", "UDP", "HTTP", "HTTPS"]),
            "port": random.choice([80, 443, 8080, 8443, 502, 1883]),
            "requests_per_second": rps,
            "bytes_transferred": rps * random.randint(100, 1500),
            "packet_count": rps * random.randint(1, 5),
            "response_time_ms": random.randint(5, 50) if not is_attack else random.randint(500, 5000),
            "severity": severity,
            "suspicious": is_attack,
        }

    def _make_connection_attempt(self, device: dict, now: datetime, is_suspicious: bool = False) -> dict:
        if is_suspicious:
            port = random.choice([4444, 5555, 6666, 31337, 8888])
            source_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            severity = "high"
        else:
            port = random.choice([443, 80, 8883, 1883, 502])
            source_ip = f"10.{device['zone_id'][-1]}.{random.randint(1,10)}.{random.randint(1,254)}"
            severity = "low"

        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "connection_attempt",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "source_ip": source_ip,
            "destination_port": port,
            "connection_status": random.choice(["established", "rejected", "timeout"]) if is_suspicious else "established",
            "protocol": "TCP",
            "severity": severity,
            "suspicious": is_suspicious,
        }

    # ── Attack Traffic Generation ──

    def trigger_attack(self, attack_type: str, zone_id: str, intensity: float = 0.8, duration: int = 30) -> Dict[str, Any]:
        """
        Trigger a simulated attack on a specific zone.
        
        attack_type: ddos_flood | malware_infection | firmware_tampering | reconnaissance
        zone_id: target zone ID (e.g. "SL-ZONE-A")
        intensity: 0.0 to 1.0
        duration: seconds
        """
        zone = next((z for z in (self.zones + self.custom_zones) if z["id"] == zone_id), None)
        if not zone:
            return {"error": f"Zone {zone_id} not found"}

        attack = {
            "attack_id": str(uuid.uuid4()),
            "type": attack_type,
            "zone": zone_id,
            "zone_name": zone["name"],
            "intensity": intensity,
            "duration": duration,
            "start_time": time.time(),
            "end_time": time.time() + duration,
        }

        with self._attack_lock:
            self.active_attacks.append(attack)

        logger.warning(f"Attack triggered: {attack_type} on {zone_id} (intensity={intensity}, duration={duration}s)")

        # Publish attack-start alert
        alert = {
            "event_id": str(uuid.uuid4()),
            "event_type": "attack_simulation_started",
            "timestamp": datetime.now().isoformat(),
            "attack_id": attack["attack_id"],
            "attack_type": attack_type,
            "target_zone": zone_id,
            "target_zone_name": zone["name"],
            "intensity": intensity,
            "duration_seconds": duration,
            "severity": "critical",
            "suspicious": True,
        }
        self._publish("cyber_alerts", f"attack_{attack['attack_id']}", alert)

        return {"status": "attack_triggered", "attack": attack}

    def _generate_attack_traffic(self, attack: Dict[str, Any]):
        """Generate attack-specific traffic based on type."""
        zone_id = attack["zone"]
        intensity = attack["intensity"]
        zone_devices = [d for d in self.devices.values() if d["zone_id"] == zone_id]

        if not zone_devices:
            return

        now = datetime.now()
        attack_type = attack["type"]

        # Number of events per tick scales with intensity
        event_count = max(1, int(intensity * 8))
        targets = random.choices(zone_devices, k=event_count)

        for device in targets:
            if attack_type == "ddos_flood":
                self._gen_ddos_event(device, now, intensity)
            elif attack_type == "malware_infection":
                self._gen_malware_event(device, now, intensity)
            elif attack_type == "firmware_tampering":
                self._gen_firmware_event(device, now, intensity)
            elif attack_type == "reconnaissance":
                self._gen_recon_event(device, now, intensity)

    def _gen_ddos_event(self, device: dict, now: datetime, intensity: float):
        """DDoS flood — high RPS from many external IPs."""
        event = self._make_network_traffic(device, now, is_attack=True)
        event["requests_per_second"] = int(event["requests_per_second"] * intensity * 2)
        event["attack_type"] = random.choice(["HTTP Flood", "SYN Flood", "UDP Flood", "Volumetric"])
        self._publish("network_events", device["device_id"], event)

    def _gen_malware_event(self, device: dict, now: datetime, intensity: float):
        """Malware — suspicious process, file encryption, C2 communication."""
        event_variant = random.choice(["process_execution", "file_system_change", "device_behavior"])

        if event_variant == "process_execution":
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "process_execution",
                "timestamp": now.isoformat(),
                "device_id": device["device_id"],
                "zone_id": device["zone_id"],
                "zone_name": device["zone_name"],
                "process_name": random.choice(["cryptominer.exe", "keylogger.bin", "backdoor.sh", "ransomware.elf"]),
                "cpu_usage": random.randint(80, 100),
                "memory_usage": random.randint(70, 95),
                "severity": "critical",
                "suspicious": True,
            }
            self._publish("device_events", device["device_id"], event)

        elif event_variant == "file_system_change":
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "file_system_change",
                "timestamp": now.isoformat(),
                "device_id": device["device_id"],
                "zone_id": device["zone_id"],
                "zone_name": device["zone_name"],
                "files_modified": random.randint(50, 500),
                "extensions_changed": random.sample([".enc", ".locked", ".crypto", ".crypt"], 2),
                "encryption_rate": round(random.uniform(50, 200) * intensity, 1),
                "severity": "critical",
                "suspicious": True,
            }
            self._publish("device_events", device["device_id"], event)

        elif event_variant == "device_behavior":
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "device_behavior",
                "timestamp": now.isoformat(),
                "device_id": device["device_id"],
                "zone_id": device["zone_id"],
                "zone_name": device["zone_name"],
                "outbound_connections": random.randint(30, 100),
                "c2_port_detected": random.choice([4444, 5555, 31337]),
                "data_exfiltration_mb": round(random.uniform(10, 500) * intensity, 1),
                "severity": "critical",
                "suspicious": True,
            }
            self._publish("device_events", device["device_id"], event)

    def _gen_firmware_event(self, device: dict, now: datetime, intensity: float):
        """Firmware tampering — integrity check failures."""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "firmware_check",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "firmware_version": device["firmware_version"],
            "integrity_check": "FAILED",
            "checksum_expected": "abc123def456",
            "checksum_actual": f"tampered_{uuid.uuid4().hex[:8]}",
            "tampered": True,
            "severity": "critical",
            "suspicious": True,
        }
        self._publish("device_events", device["device_id"], event)

    def _gen_recon_event(self, device: dict, now: datetime, intensity: float):
        """Reconnaissance — port scanning and probing."""
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "connection_attempt",
            "timestamp": now.isoformat(),
            "device_id": device["device_id"],
            "zone_id": device["zone_id"],
            "zone_name": device["zone_name"],
            "source_ip": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "destination_port": random.choice([22, 23, 80, 443, 502, 1883, 4444, 5555, 8080, 8443, 31337]),
            "connection_status": random.choice(["rejected", "timeout", "established"]),
            "scan_type": random.choice(["port_scan", "service_probe", "vulnerability_scan"]),
            "protocol": random.choice(["TCP", "UDP"]),
            "severity": "high",
            "suspicious": True,
        }
        self._publish("network_events", device["device_id"], event)


# Singleton instance
network_simulator = NetworkSimulator()
