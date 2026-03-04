import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CybersecurityConfig:
    """
    Centralized configuration for the Cybersecurity service.
    All thresholds are mutable at runtime via update methods.
    On restart, values reset to defaults (or env var overrides).
    """

    def __init__(self):
        self._load_defaults()

    def _load_defaults(self):
        """Load default configuration values (or from env vars)."""

        # ── Groq / LLM ──
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        self.GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0"))

        # ── Kafka ──
        self.KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.KAFKA_TOPIC_NETWORK: str = os.getenv("KAFKA_TOPIC_NETWORK", "network_events")
        self.KAFKA_TOPIC_DEVICE: str = os.getenv("KAFKA_TOPIC_DEVICE", "device_events")
        self.KAFKA_TOPIC_ALERTS: str = os.getenv("KAFKA_TOPIC_ALERTS", "cyber_alerts")
        self.KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "cybersecurity_agents")

        # ── Agent Timeouts ──
        self.AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "30"))
        self.DDOS_AGENT_TIMEOUT: int = int(os.getenv("DDOS_AGENT_TIMEOUT", "30"))
        self.MALWARE_AGENT_TIMEOUT: int = int(os.getenv("MALWARE_AGENT_TIMEOUT", "30"))

        # ── DDoS Detection Thresholds ──
        self.DDOS_NORMAL_RPS_MIN: int = int(os.getenv("DDOS_NORMAL_RPS_MIN", "100"))
        self.DDOS_NORMAL_RPS_MAX: int = int(os.getenv("DDOS_NORMAL_RPS_MAX", "500"))
        self.DDOS_MODERATE_RPS: int = int(os.getenv("DDOS_MODERATE_RPS", "1000"))
        self.DDOS_HIGH_RPS: int = int(os.getenv("DDOS_HIGH_RPS", "2000"))
        self.DDOS_CRITICAL_RPS: int = int(os.getenv("DDOS_CRITICAL_RPS", "5000"))
        self.DDOS_SYN_FLOOD_THRESHOLD: int = int(os.getenv("DDOS_SYN_FLOOD_THRESHOLD", "1000"))
        self.DDOS_HTTP_FLOOD_THRESHOLD: int = int(os.getenv("DDOS_HTTP_FLOOD_THRESHOLD", "2000"))
        self.DDOS_PACKET_SIZE_ANOMALY_MIN: int = int(os.getenv("DDOS_PACKET_SIZE_ANOMALY_MIN", "64"))
        self.DDOS_PACKET_SIZE_ANOMALY_MAX: int = int(os.getenv("DDOS_PACKET_SIZE_ANOMALY_MAX", "9000"))
        self.DDOS_REQUESTS_PER_IP_NORMAL: int = int(os.getenv("DDOS_REQUESTS_PER_IP_NORMAL", "50"))
        self.DDOS_REQUESTS_PER_IP_SUSPICIOUS: int = int(os.getenv("DDOS_REQUESTS_PER_IP_SUSPICIOUS", "200"))
        self.DDOS_UNIQUE_IPS_NORMAL: int = int(os.getenv("DDOS_UNIQUE_IPS_NORMAL", "100"))
        self.DDOS_UNIQUE_IPS_ATTACK: int = int(os.getenv("DDOS_UNIQUE_IPS_ATTACK", "10000"))
        self.DDOS_GEO_CONCENTRATION_THRESHOLD: float = float(os.getenv("DDOS_GEO_CONCENTRATION_THRESHOLD", "0.8"))
        self.DDOS_RESPONSE_TIME_NORMAL_MS: int = int(os.getenv("DDOS_RESPONSE_TIME_NORMAL_MS", "200"))
        self.DDOS_FAILED_REQUEST_RATE: float = float(os.getenv("DDOS_FAILED_REQUEST_RATE", "0.1"))
        self.DDOS_DETECTION_WINDOW: int = int(os.getenv("DDOS_DETECTION_WINDOW", "300"))

        # ── Malware Detection Thresholds ──
        self.MALWARE_FILE_ENCRYPTION_RATE_THRESHOLD: int = int(os.getenv("MALWARE_FILE_ENCRYPTION_RATE_THRESHOLD", "100"))
        self.MALWARE_SUSPICIOUS_PROCESS_COUNT: int = int(os.getenv("MALWARE_SUSPICIOUS_PROCESS_COUNT", "5"))
        self.MALWARE_CPU_USAGE_SUSPICIOUS: int = int(os.getenv("MALWARE_CPU_USAGE_SUSPICIOUS", "95"))
        self.MALWARE_MEMORY_USAGE_SUSPICIOUS: int = int(os.getenv("MALWARE_MEMORY_USAGE_SUSPICIOUS", "90"))
        self.MALWARE_OUTBOUND_CONNECTIONS_THRESHOLD: int = int(os.getenv("MALWARE_OUTBOUND_CONNECTIONS_THRESHOLD", "50"))
        self.MALWARE_FILE_MODIFICATIONS_THRESHOLD: int = int(os.getenv("MALWARE_FILE_MODIFICATIONS_THRESHOLD", "100"))
        self.MALWARE_NETWORK_UPLOAD_THRESHOLD_MB: int = int(os.getenv("MALWARE_NETWORK_UPLOAD_THRESHOLD_MB", "500"))

        self.MALWARE_C2_COMMUNICATION_PORTS: List[int] = [4444, 5555, 6666, 8888, 9999, 1234, 31337]
        self.MALWARE_SUSPICIOUS_EXTENSIONS: List[str] = [".enc", ".locked", ".crypto", ".crypt", ".pay", ".ransom"]
        self.MALWARE_SUSPICIOUS_PROCESSES: List[str] = [
            "cryptominer", "keylogger", "backdoor", "rootkit",
            "trojan", "ransomware", "spyware", "worm",
        ]
        self.MALWARE_KNOWN_FAMILIES: List[str] = [
            "WannaCry", "Mirai", "Emotet", "TrickBot",
            "Ryuk", "REvil", "Conti", "BlackCat",
        ]

    # ── Getters (for API responses) ──

    def get_ddos_config(self) -> Dict[str, Any]:
        """Return all DDoS config as a dict for the admin dashboard."""
        return {
            "thresholds": {
                "normal_rps_min": self.DDOS_NORMAL_RPS_MIN,
                "normal_rps_max": self.DDOS_NORMAL_RPS_MAX,
                "moderate_rps": self.DDOS_MODERATE_RPS,
                "high_rps": self.DDOS_HIGH_RPS,
                "critical_rps": self.DDOS_CRITICAL_RPS,
                "syn_flood_threshold": self.DDOS_SYN_FLOOD_THRESHOLD,
                "http_flood_threshold": self.DDOS_HTTP_FLOOD_THRESHOLD,
                "packet_size_anomaly_min": self.DDOS_PACKET_SIZE_ANOMALY_MIN,
                "packet_size_anomaly_max": self.DDOS_PACKET_SIZE_ANOMALY_MAX,
                "requests_per_ip_normal": self.DDOS_REQUESTS_PER_IP_NORMAL,
                "requests_per_ip_suspicious": self.DDOS_REQUESTS_PER_IP_SUSPICIOUS,
                "unique_ips_normal": self.DDOS_UNIQUE_IPS_NORMAL,
                "unique_ips_attack": self.DDOS_UNIQUE_IPS_ATTACK,
                "geo_concentration_threshold": self.DDOS_GEO_CONCENTRATION_THRESHOLD,
                "response_time_normal_ms": self.DDOS_RESPONSE_TIME_NORMAL_MS,
                "failed_request_rate": self.DDOS_FAILED_REQUEST_RATE,
            },
            "detection_window": self.DDOS_DETECTION_WINDOW,
            "agent_timeout": self.DDOS_AGENT_TIMEOUT,
            "attack_types": [
                "HTTP Flood", "SYN Flood", "UDP Flood",
                "Volumetric Attack", "Slowloris", "DNS Amplification",
            ],
        }

    def get_malware_config(self) -> Dict[str, Any]:
        """Return all Malware config as a dict for the admin dashboard."""
        return {
            "thresholds": {
                "file_encryption_rate": self.MALWARE_FILE_ENCRYPTION_RATE_THRESHOLD,
                "suspicious_process_count": self.MALWARE_SUSPICIOUS_PROCESS_COUNT,
                "cpu_usage_threshold": self.MALWARE_CPU_USAGE_SUSPICIOUS,
                "memory_usage_threshold": self.MALWARE_MEMORY_USAGE_SUSPICIOUS,
                "outbound_connections": self.MALWARE_OUTBOUND_CONNECTIONS_THRESHOLD,
                "file_modifications": self.MALWARE_FILE_MODIFICATIONS_THRESHOLD,
                "network_upload_mb": self.MALWARE_NETWORK_UPLOAD_THRESHOLD_MB,
            },
            "c2_suspicious_ports": self.MALWARE_C2_COMMUNICATION_PORTS,
            "suspicious_extensions": self.MALWARE_SUSPICIOUS_EXTENSIONS,
            "suspicious_processes": self.MALWARE_SUSPICIOUS_PROCESSES,
            "known_families": self.MALWARE_KNOWN_FAMILIES,
            "agent_timeout": self.MALWARE_AGENT_TIMEOUT,
            "detection_types": [
                "Ransomware", "Trojan", "Botnet",
                "Spyware", "Rootkit", "Worm", "Cryptominer",
            ],
        }

    # ── Updaters (called by PUT endpoints) ──

    def update_ddos_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update DDoS thresholds from admin dashboard. Returns updated config."""
        field_map = {
            "normal_rps_min": ("DDOS_NORMAL_RPS_MIN", int),
            "normal_rps_max": ("DDOS_NORMAL_RPS_MAX", int),
            "moderate_rps": ("DDOS_MODERATE_RPS", int),
            "high_rps": ("DDOS_HIGH_RPS", int),
            "critical_rps": ("DDOS_CRITICAL_RPS", int),
            "syn_flood_threshold": ("DDOS_SYN_FLOOD_THRESHOLD", int),
            "http_flood_threshold": ("DDOS_HTTP_FLOOD_THRESHOLD", int),
            "packet_size_anomaly_min": ("DDOS_PACKET_SIZE_ANOMALY_MIN", int),
            "packet_size_anomaly_max": ("DDOS_PACKET_SIZE_ANOMALY_MAX", int),
            "requests_per_ip_normal": ("DDOS_REQUESTS_PER_IP_NORMAL", int),
            "requests_per_ip_suspicious": ("DDOS_REQUESTS_PER_IP_SUSPICIOUS", int),
            "unique_ips_normal": ("DDOS_UNIQUE_IPS_NORMAL", int),
            "unique_ips_attack": ("DDOS_UNIQUE_IPS_ATTACK", int),
            "geo_concentration_threshold": ("DDOS_GEO_CONCENTRATION_THRESHOLD", float),
            "response_time_normal_ms": ("DDOS_RESPONSE_TIME_NORMAL_MS", int),
            "failed_request_rate": ("DDOS_FAILED_REQUEST_RATE", float),
            "detection_window": ("DDOS_DETECTION_WINDOW", int),
            "agent_timeout": ("DDOS_AGENT_TIMEOUT", int),
        }
        updated = []
        for key, value in data.items():
            if key in field_map:
                attr_name, cast_fn = field_map[key]
                setattr(self, attr_name, cast_fn(value))
                updated.append(key)
                logger.info(f"DDoS config updated: {key} = {value}")
        return {"updated_fields": updated, "config": self.get_ddos_config()}

    def update_malware_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update Malware thresholds from admin dashboard. Returns updated config."""
        field_map = {
            "file_encryption_rate": ("MALWARE_FILE_ENCRYPTION_RATE_THRESHOLD", int),
            "suspicious_process_count": ("MALWARE_SUSPICIOUS_PROCESS_COUNT", int),
            "cpu_usage_threshold": ("MALWARE_CPU_USAGE_SUSPICIOUS", int),
            "memory_usage_threshold": ("MALWARE_MEMORY_USAGE_SUSPICIOUS", int),
            "outbound_connections": ("MALWARE_OUTBOUND_CONNECTIONS_THRESHOLD", int),
            "file_modifications": ("MALWARE_FILE_MODIFICATIONS_THRESHOLD", int),
            "network_upload_mb": ("MALWARE_NETWORK_UPLOAD_THRESHOLD_MB", int),
            "agent_timeout": ("MALWARE_AGENT_TIMEOUT", int),
        }
        updated = []
        for key, value in data.items():
            if key in field_map:
                attr_name, cast_fn = field_map[key]
                setattr(self, attr_name, cast_fn(value))
                updated.append(key)
                logger.info(f"Malware config updated: {key} = {value}")

        # Handle list-type fields
        if "c2_suspicious_ports" in data and isinstance(data["c2_suspicious_ports"], list):
            self.MALWARE_C2_COMMUNICATION_PORTS = [int(p) for p in data["c2_suspicious_ports"]]
            updated.append("c2_suspicious_ports")
        if "suspicious_extensions" in data and isinstance(data["suspicious_extensions"], list):
            self.MALWARE_SUSPICIOUS_EXTENSIONS = list(data["suspicious_extensions"])
            updated.append("suspicious_extensions")
        if "suspicious_processes" in data and isinstance(data["suspicious_processes"], list):
            self.MALWARE_SUSPICIOUS_PROCESSES = list(data["suspicious_processes"])
            updated.append("suspicious_processes")
        if "known_families" in data and isinstance(data["known_families"], list):
            self.MALWARE_KNOWN_FAMILIES = list(data["known_families"])
            updated.append("known_families")

        return {"updated_fields": updated, "config": self.get_malware_config()}

    def reset_to_defaults(self):
        """Reset all config to defaults (re-reads env vars)."""
        self._load_defaults()
        logger.info("All configuration reset to defaults")

    # ── Utility Methods ──

    def get_kafka_config(self) -> Dict[str, str]:
        return {
            "bootstrap_servers": self.KAFKA_BOOTSTRAP_SERVERS,
            "topic_network": self.KAFKA_TOPIC_NETWORK,
            "topic_device": self.KAFKA_TOPIC_DEVICE,
            "topic_alerts": self.KAFKA_TOPIC_ALERTS,
            "consumer_group": self.KAFKA_CONSUMER_GROUP,
        }

    def get_groq_config(self) -> Dict[str, Any]:
        return {
            "api_key": self.GROQ_API_KEY,
            "model": self.GROQ_MODEL,
            "temperature": self.GROQ_TEMPERATURE,
        }


# Singleton instance — imported by agents and main.py
config = CybersecurityConfig()