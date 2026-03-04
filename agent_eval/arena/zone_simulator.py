"""
Zone Simulator — Simulates a realistic segment of Mumbai's smart lighting grid.

Each zone container runs this script, generating:
- Smart pole telemetry (ambient light, power, motion)
- Gateway aggregation events
- Zone controller status updates
- Network traffic events (HTTP, MQTT, CoAP)

Traffic follows diurnal patterns and zone-specific profiles.
Configured entirely via environment variables set in docker-compose.yml.
"""

import os
import sys
import json
import time
import random
import math
import signal
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("zone-simulator")

# ── Try to import Kafka; fallback to stdout for testing ──
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed, falling back to stdout logging")


# ── Zone Configuration ─────────────────────────────────────

@dataclass
class SmartPole:
    """Represents a single smart lighting pole with sensors."""
    pole_id: str
    zone_id: str
    gateway_id: str
    latitude: float
    longitude: float
    firmware_version: str = "2.1.4"
    ip_address: str = ""
    mac_address: str = ""
    status: str = "online"
    brightness: int = 100
    power_watts: float = 150.0
    ambient_lux: float = 0.0
    motion_detected: bool = False
    uptime_hours: float = 0.0
    last_seen: str = ""

    def __post_init__(self):
        if not self.ip_address:
            self.ip_address = f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        if not self.mac_address:
            self.mac_address = ":".join(f"{random.randint(0,255):02x}" for _ in range(6))


@dataclass
class Gateway:
    """Aggregates data from multiple smart poles via mesh network."""
    gateway_id: str
    zone_id: str
    ip_address: str = ""
    connected_poles: List[str] = field(default_factory=list)
    protocol: str = "zigbee"  # zigbee, lora, wifi
    uptime_hours: float = 0.0

    def __post_init__(self):
        if not self.ip_address:
            self.ip_address = f"10.0.{random.randint(1,254)}.1"


@dataclass
class ZoneController:
    """Central controller for the zone — publishes to Kafka."""
    zone_id: str
    zone_name: str
    security_level: int  # IEC 62443 SL (1-4)
    num_poles: int
    num_gateways: int
    traffic_profile: str
    poles: List[SmartPole] = field(default_factory=list)
    gateways: List[Gateway] = field(default_factory=list)


# ── Traffic Profiles ───────────────────────────────────────
# Diurnal traffic multiplier curves (24 hours)
# Value = traffic multiplier at that hour

TRAFFIC_PROFILES = {
    "commercial_high": {
        "description": "BKC Commercial - peaks during business hours",
        "base_rps": 50,
        "hourly_multiplier": [
            0.1, 0.1, 0.1, 0.1, 0.15, 0.3,   # 00-05: very low
            0.5, 0.8, 1.0, 1.0, 1.0, 0.9,     # 06-11: ramp up
            0.8, 1.0, 1.0, 1.0, 0.9, 0.7,     # 12-17: business peak
            0.5, 0.4, 0.3, 0.2, 0.15, 0.1,    # 18-23: wind down
        ],
        "sensor_interval_sec": 5,
    },
    "critical_healthcare": {
        "description": "Hospital - 24/7 steady with slight peaks",
        "base_rps": 40,
        "hourly_multiplier": [
            0.7, 0.6, 0.6, 0.6, 0.6, 0.7,    # 00-05: night shift
            0.8, 0.9, 1.0, 1.0, 1.0, 1.0,     # 06-11: morning rounds
            1.0, 0.9, 1.0, 1.0, 1.0, 0.9,     # 12-17: afternoon
            0.8, 0.8, 0.7, 0.7, 0.7, 0.7,     # 18-23: evening
        ],
        "sensor_interval_sec": 3,  # More frequent for critical zone
    },
    "critical_transport": {
        "description": "Airport - peaks at dawn/dusk, steady mid-day",
        "base_rps": 60,
        "hourly_multiplier": [
            0.4, 0.3, 0.3, 0.4, 0.6, 0.9,    # 00-05: early flights
            1.0, 1.0, 0.9, 0.8, 0.8, 0.8,     # 06-11: morning peak
            0.7, 0.8, 0.9, 1.0, 1.0, 1.0,     # 12-17: afternoon peak
            0.9, 0.8, 0.7, 0.6, 0.5, 0.4,     # 18-23: evening
        ],
        "sensor_interval_sec": 3,
    },
    "industrial": {
        "description": "Port area - shift-based with 3 shifts",
        "base_rps": 35,
        "hourly_multiplier": [
            0.3, 0.3, 0.3, 0.3, 0.3, 0.5,    # 00-05: night shift low
            0.8, 1.0, 1.0, 1.0, 1.0, 0.9,     # 06-11: day shift
            0.8, 1.0, 1.0, 1.0, 0.8, 0.6,     # 12-17: afternoon shift
            0.5, 0.4, 0.3, 0.3, 0.3, 0.3,     # 18-23: night shift
        ],
        "sensor_interval_sec": 10,
    },
    "institutional": {
        "description": "School - peaks during school hours only",
        "base_rps": 20,
        "hourly_multiplier": [
            0.1, 0.1, 0.1, 0.1, 0.1, 0.2,    # 00-05: minimal
            0.3, 0.6, 1.0, 1.0, 1.0, 1.0,     # 06-11: school hours
            1.0, 1.0, 0.8, 0.5, 0.3, 0.2,     # 12-17: after school
            0.15, 0.1, 0.1, 0.1, 0.1, 0.1,    # 18-23: minimal
        ],
        "sensor_interval_sec": 15,
    },
    "residential": {
        "description": "Residential - peaks morning and evening",
        "base_rps": 30,
        "hourly_multiplier": [
            0.2, 0.15, 0.1, 0.1, 0.1, 0.2,   # 00-05: sleeping
            0.4, 0.7, 0.8, 0.5, 0.3, 0.3,     # 06-11: morning activity
            0.3, 0.3, 0.3, 0.4, 0.5, 0.7,     # 12-17: returning home
            1.0, 1.0, 0.9, 0.7, 0.5, 0.3,     # 18-23: evening peak
        ],
        "sensor_interval_sec": 10,
    },
    "highway": {
        "description": "Highway - peaks during commute hours",
        "base_rps": 45,
        "hourly_multiplier": [
            0.2, 0.15, 0.1, 0.15, 0.2, 0.5,  # 00-05: very light
            0.8, 1.0, 1.0, 0.8, 0.6, 0.5,     # 06-11: morning commute
            0.5, 0.5, 0.5, 0.6, 0.8, 1.0,     # 12-17: evening commute
            1.0, 0.8, 0.6, 0.4, 0.3, 0.2,     # 18-23: winding down
        ],
        "sensor_interval_sec": 5,
    },
}

# Mumbai zone coordinates (approximate real-world locations)
ZONE_COORDINATES = {
    "bkc_commercial":    {"lat_base": 19.0650, "lon_base": 72.8685, "spread": 0.005},
    "reliance_hospital": {"lat_base": 19.0157, "lon_base": 72.8302, "spread": 0.002},
    "airport":           {"lat_base": 19.0896, "lon_base": 72.8656, "spread": 0.008},
    "port_area":         {"lat_base": 18.9322, "lon_base": 72.8434, "spread": 0.004},
    "school_complex":    {"lat_base": 19.0760, "lon_base": 72.8777, "spread": 0.002},
    "residential":       {"lat_base": 19.1197, "lon_base": 72.8464, "spread": 0.006},
    "highway_corridor":  {"lat_base": 19.1060, "lon_base": 72.8570, "spread": 0.015},
}


class ZoneSimulator:
    """
    Simulates a complete zone of Mumbai's smart lighting grid.
    Generates realistic traffic, sensor data, and device events.
    """

    def __init__(self):
        # Read config from environment
        self.zone_id = os.getenv("ZONE_ID", "test_zone")
        self.zone_name = os.getenv("ZONE_NAME", "Test Zone")
        self.num_poles = int(os.getenv("NUM_POLES", "5"))
        self.num_gateways = int(os.getenv("NUM_GATEWAYS", "1"))
        self.security_level = int(os.getenv("SECURITY_LEVEL", "2"))
        self.traffic_profile_name = os.getenv("TRAFFIC_PROFILE", "residential")
        self.kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        self.traffic_profile = TRAFFIC_PROFILES.get(
            self.traffic_profile_name, TRAFFIC_PROFILES["residential"]
        )
        coords = ZONE_COORDINATES.get(
            self.zone_id, {"lat_base": 19.07, "lon_base": 72.87, "spread": 0.005}
        )

        # Initialize zone infrastructure
        self.controller = self._build_zone(coords)
        self.producer: Optional[Any] = None
        self.running = True
        self.start_time = time.time()
        self.event_count = 0

        logger.info(
            f"Zone '{self.zone_name}' initialized: "
            f"{self.num_poles} poles, {self.num_gateways} gateways, "
            f"SL-{self.security_level}, profile={self.traffic_profile_name}"
        )

    def _build_zone(self, coords: Dict) -> ZoneController:
        """Create poles, gateways, and controller for this zone."""
        gateways = []
        poles = []
        poles_per_gw = max(1, self.num_poles // self.num_gateways)

        for gw_idx in range(self.num_gateways):
            gw = Gateway(
                gateway_id=f"{self.zone_id}_gw_{gw_idx}",
                zone_id=self.zone_id,
                protocol=random.choice(["zigbee", "lora", "wifi"]),
            )
            gateways.append(gw)

            # Create poles assigned to this gateway
            for p_idx in range(poles_per_gw):
                pole_num = gw_idx * poles_per_gw + p_idx
                if pole_num >= self.num_poles:
                    break
                pole = SmartPole(
                    pole_id=f"{self.zone_id}_pole_{pole_num:03d}",
                    zone_id=self.zone_id,
                    gateway_id=gw.gateway_id,
                    latitude=coords["lat_base"] + random.uniform(-coords["spread"], coords["spread"]),
                    longitude=coords["lon_base"] + random.uniform(-coords["spread"], coords["spread"]),
                )
                poles.append(pole)
                gw.connected_poles.append(pole.pole_id)

        return ZoneController(
            zone_id=self.zone_id,
            zone_name=self.zone_name,
            security_level=self.security_level,
            num_poles=self.num_poles,
            num_gateways=self.num_gateways,
            traffic_profile=self.traffic_profile_name,
            poles=poles,
            gateways=gateways,
        )

    def _connect_kafka(self):
        """Connect to Kafka/Redpanda broker with retries."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available, events will be logged to stdout")
            return

        for attempt in range(30):
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
                logger.warning(f"Kafka connection attempt {attempt+1}/30 failed: {e}")
                time.sleep(2)

        logger.error("Failed to connect to Kafka after 30 attempts")
        sys.exit(1)

    def _publish(self, topic: str, event: Dict[str, Any]):
        """Publish event to Kafka topic or stdout."""
        self.event_count += 1
        if self.producer:
            try:
                self.producer.send(topic, value=event)
            except Exception as e:
                logger.error(f"Failed to publish to {topic}: {e}")
        else:
            logger.debug(f"[{topic}] {json.dumps(event, default=str)[:200]}")

    def _get_diurnal_multiplier(self) -> float:
        """Get traffic multiplier based on current hour (IST)."""
        # Use IST (UTC+5:30)
        utc_now = datetime.now(timezone.utc)
        ist_hour = (utc_now.hour + 5) % 24  # Simplified IST offset
        ist_minute = utc_now.minute + 30
        if ist_minute >= 60:
            ist_hour = (ist_hour + 1) % 24
            ist_minute -= 60

        # Interpolate between hours for smooth transitions
        next_hour = (ist_hour + 1) % 24
        fraction = ist_minute / 60.0
        current_mult = self.traffic_profile["hourly_multiplier"][ist_hour]
        next_mult = self.traffic_profile["hourly_multiplier"][next_hour]
        return current_mult + (next_mult - current_mult) * fraction

    def _generate_sensor_event(self, pole: SmartPole) -> Dict[str, Any]:
        """Generate a sensor telemetry event from a smart pole."""
        mult = self._get_diurnal_multiplier()
        # Ambient light inversely correlates with brightness needed
        ist_hour = (datetime.now(timezone.utc).hour + 5) % 24
        ambient_lux = max(0, 500 * math.sin(math.pi * (ist_hour - 6) / 12)) if 6 <= ist_hour <= 18 else random.uniform(0, 5)

        pole.ambient_lux = ambient_lux + random.gauss(0, 10)
        pole.brightness = max(10, min(100, int(100 - ambient_lux / 5)))
        pole.power_watts = pole.brightness * 1.5 + random.gauss(0, 5)
        pole.motion_detected = random.random() < (0.3 * mult)
        pole.uptime_hours = (time.time() - self.start_time) / 3600
        pole.last_seen = datetime.now(timezone.utc).isoformat()

        return {
            "event_type": "sensor_telemetry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "security_level": self.security_level,
            "device_id": pole.pole_id,
            "device_type": "smart_pole",
            "gateway_id": pole.gateway_id,
            "ip_address": pole.ip_address,
            "mac_address": pole.mac_address,
            "firmware_version": pole.firmware_version,
            "location": {"lat": pole.latitude, "lon": pole.longitude},
            "metrics": {
                "ambient_lux": round(pole.ambient_lux, 2),
                "brightness_pct": pole.brightness,
                "power_watts": round(pole.power_watts, 2),
                "motion_detected": pole.motion_detected,
                "temperature_c": round(25 + random.gauss(0, 3), 1),
                "uptime_hours": round(pole.uptime_hours, 2),
            },
            "status": pole.status,
        }

    def _generate_network_event(self, pole: SmartPole) -> Dict[str, Any]:
        """Generate a network traffic event (HTTP request to lighting API)."""
        mult = self._get_diurnal_multiplier()
        endpoints = [
            "/api/v1/lights/status", "/api/v1/lights/brightness",
            "/api/v1/lights/schedule", "/api/v1/sensors/ambient",
            "/api/v1/health", "/api/v1/firmware/check",
            "/api/v1/config/zone", "/api/v1/alerts/check",
        ]
        methods = ["GET"] * 7 + ["POST"] * 2 + ["PUT"]
        status_codes = [200] * 20 + [201] * 3 + [304] * 5 + [400] + [500]

        return {
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "security_level": self.security_level,
            "source_ip": pole.ip_address,
            "source_mac": pole.mac_address,
            "destination_ip": "10.0.0.1",
            "destination_port": random.choice([80, 443, 8080, 1883]),
            "protocol": random.choice(["HTTP", "HTTPS", "MQTT", "CoAP"]),
            "method": random.choice(methods),
            "endpoint": random.choice(endpoints),
            "status_code": random.choice(status_codes),
            "response_time_ms": round(random.gauss(50, 15) / mult if mult > 0.1 else 200, 1),
            "bytes_sent": random.randint(100, 2000),
            "bytes_received": random.randint(200, 5000),
            "packet_size": random.randint(200, 1500),
            "user_agent": f"SmartPole/{pole.firmware_version}",
            "device_id": pole.pole_id,
        }

    def _generate_device_event(self, pole: SmartPole) -> Dict[str, Any]:
        """Generate a device lifecycle event (startup, config change, etc.)."""
        event_types = [
            ("heartbeat", 0.7),
            ("config_sync", 0.1),
            ("firmware_check", 0.05),
            ("brightness_change", 0.1),
            ("motion_trigger", 0.05),
        ]
        event_subtype = random.choices(
            [e[0] for e in event_types],
            weights=[e[1] for e in event_types],
        )[0]

        return {
            "event_type": "device_event",
            "event_subtype": event_subtype,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "security_level": self.security_level,
            "device_id": pole.pole_id,
            "device_type": "smart_pole",
            "gateway_id": pole.gateway_id,
            "ip_address": pole.ip_address,
            "firmware_version": pole.firmware_version,
            "status": pole.status,
            "details": {
                "uptime_hours": round(pole.uptime_hours, 2),
                "brightness": pole.brightness,
                "power_watts": round(pole.power_watts, 2),
            },
        }

    def run(self):
        """Main simulation loop — generates events at zone-specific rates."""
        self._connect_kafka()
        sensor_interval = self.traffic_profile["sensor_interval_sec"]
        last_sensor_time = 0
        last_stats_time = time.time()

        logger.info(f"Starting simulation for zone '{self.zone_name}'...")

        while self.running:
            try:
                now = time.time()
                mult = self._get_diurnal_multiplier()

                # ── Sensor telemetry (periodic) ──
                if now - last_sensor_time >= sensor_interval:
                    for pole in self.controller.poles:
                        event = self._generate_sensor_event(pole)
                        self._publish("sensor_data", event)
                    last_sensor_time = now

                # ── Network traffic (rate-based) ──
                base_rps = self.traffic_profile["base_rps"]
                current_rps = max(1, int(base_rps * mult))
                events_this_tick = max(1, current_rps // 10)  # 100ms tick
                for _ in range(events_this_tick):
                    pole = random.choice(self.controller.poles)
                    event = self._generate_network_event(pole)
                    self._publish("network_events", event)

                # ── Device events (occasional) ──
                if random.random() < 0.1 * mult:
                    pole = random.choice(self.controller.poles)
                    event = self._generate_device_event(pole)
                    self._publish("device_events", event)

                # ── Stats logging (every 60 seconds) ──
                if now - last_stats_time >= 60:
                    logger.info(
                        f"Zone '{self.zone_name}': {self.event_count} events generated, "
                        f"current_rps={current_rps}, multiplier={mult:.2f}"
                    )
                    last_stats_time = now

                # Sleep for ~100ms between ticks
                time.sleep(0.1)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                time.sleep(1)

        logger.info(f"Zone '{self.zone_name}' stopped. Total events: {self.event_count}")
        if self.producer:
            self.producer.flush()
            self.producer.close()


def main():
    simulator = ZoneSimulator()

    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        simulator.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    simulator.run()


if __name__ == "__main__":
    main()
