"""
Log Ingestion Agent — Tier 1 SOC: CEF Normalization & Semantic Compression.

Implements the 3-stage context window management pipeline from the implementation plan:
  Stage 1: Sliding Window Buffer (30-sec rolling window with 10-sec overlap)
  Stage 2: CEF Normalization + Dedup → Statistical Aggregation
  Stage 3: Context Summary (~500-800 tokens) for downstream LLM agents

Consumes raw events from Kafka topics (network_events, device_events, sensor_data)
and publishes normalized/compressed summaries to the `normalized_events` topic.

Based on:
  - RAG best practices (2024) for sliding window chunking
  - LLM log analysis (brightcoding.dev, 2025) for semantic compression
  - SIEM CEF normalization standard
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from pydantic import BaseModel
from langgraph.graph import StateGraph, END

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("log-ingestion-agent")

# ── Optional imports ──
try:
    from kafka import KafkaConsumer, KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# CEF (Common Event Format) Normalizer
# ═══════════════════════════════════════════════════════════════════════════════

class CEFNormalizer:
    """
    Converts raw zone simulator events into Common Event Format (CEF).

    CEF format: CEF:0|Vendor|Product|Version|EventClassID|Name|Severity|Extension
    We use a simplified dict-based CEF rather than string-based for programmatic use.
    """

    # Severity mapping: raw event indicators → CEF severity (0-10)
    SEVERITY_MAP = {
        "none": 0,
        "low": 3,
        "medium": 5,
        "high": 7,
        "critical": 9,
        "emergency": 10,
    }

    # Event class IDs by event type
    EVENT_CLASS_IDS = {
        "network_traffic": "NET",
        "sensor_telemetry": "SEN",
        "device_event": "DEV",
        "process_execution": "PRC",
        "file_system_change": "FSC",
        "firmware_check": "FWC",
        "device_behavior": "BHV",
        "connection_attempt": "CON",
        "scenario_marker": "MRK",
    }

    @staticmethod
    def normalize(raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw event to CEF-normalized format."""
        event_type = raw_event.get("event_type", "unknown")
        timestamp = raw_event.get("timestamp", datetime.now(timezone.utc).isoformat())
        zone_id = raw_event.get("zone_id", "unknown")
        device_id = raw_event.get("device_id", "unknown")

        # Determine severity
        severity_raw = raw_event.get("severity", "low")
        if raw_event.get("suspicious", False):
            severity_raw = max(severity_raw, "high") if isinstance(severity_raw, str) else "high"
        severity = CEFNormalizer.SEVERITY_MAP.get(
            severity_raw if isinstance(severity_raw, str) else "low", 3
        )

        # Determine event class
        event_class = CEFNormalizer.EVENT_CLASS_IDS.get(event_type, "UNK")

        # Build normalized event
        cef_event = {
            "cef_version": "0",
            "vendor": "AI_Cyber_Arena",
            "product": "SmartLightingGrid",
            "version": "1.0",
            "event_class_id": event_class,
            "event_type": event_type,
            "name": CEFNormalizer._generate_name(raw_event),
            "severity": severity,
            "timestamp": timestamp,
            "zone_id": zone_id,
            "device_id": device_id,
        }

        # Add type-specific extensions
        if event_type == "network_traffic":
            cef_event.update({
                "src_ip": raw_event.get("source_ip", ""),
                "dst_ip": raw_event.get("destination_ip", ""),
                "dst_port": raw_event.get("destination_port", 0),
                "protocol": raw_event.get("protocol", ""),
                "method": raw_event.get("method", ""),
                "endpoint": raw_event.get("endpoint", ""),
                "status_code": raw_event.get("status_code", 0),
                "response_time_ms": raw_event.get("response_time_ms", 0),
                "bytes_sent": raw_event.get("bytes_sent", 0),
                "bytes_received": raw_event.get("bytes_received", 0),
                "rps": raw_event.get("requests_per_second", 0),
            })

        elif event_type == "sensor_telemetry":
            metrics = raw_event.get("metrics", {})
            cef_event.update({
                "ambient_lux": metrics.get("ambient_lux", 0),
                "brightness_pct": metrics.get("brightness_pct", 0),
                "power_watts": metrics.get("power_watts", 0),
                "motion_detected": metrics.get("motion_detected", False),
                "temperature_c": metrics.get("temperature_c", 0),
            })

        elif event_type in ("device_event", "process_execution",
                            "file_system_change", "firmware_check",
                            "device_behavior"):
            cef_event.update({
                "event_subtype": raw_event.get("event_subtype", ""),
                "status": raw_event.get("status", ""),
                "details": raw_event.get("details", {}),
            })

        # Carry attack indicators if present
        if "attack_indicators" in raw_event:
            cef_event["attack_indicators"] = raw_event["attack_indicators"]
            cef_event["suspicious"] = True
        else:
            cef_event["suspicious"] = raw_event.get("suspicious", False)

        return cef_event

    @staticmethod
    def _generate_name(raw_event: Dict[str, Any]) -> str:
        """Generate a human-readable event name."""
        event_type = raw_event.get("event_type", "unknown")
        zone = raw_event.get("zone_id", "unknown")
        device = raw_event.get("device_id", "unknown")

        if event_type == "network_traffic":
            proto = raw_event.get("protocol", "?")
            method = raw_event.get("method", "?")
            return f"{proto} {method} from {device}"
        elif event_type == "sensor_telemetry":
            return f"Sensor reading from {device}"
        elif event_type == "device_event":
            subtype = raw_event.get("event_subtype", "unknown")
            return f"Device {subtype} on {device}"
        else:
            return f"{event_type} on {device}"


# ═══════════════════════════════════════════════════════════════════════════════
# Sliding Window Buffer
# ═══════════════════════════════════════════════════════════════════════════════

class SlidingWindowBuffer:
    """
    Time-windowed event buffer with overlap.

    Collects CEF-normalized events into 30-second rolling windows with
    10-second overlap. When a window closes, it emits the events for
    aggregation and compression.
    """

    def __init__(self, window_sec: float = 30.0, overlap_sec: float = 10.0):
        self.window_sec = window_sec
        self.overlap_sec = overlap_sec
        self.events: List[Dict[str, Any]] = []
        self.window_start: float = time.time()
        self._lock = threading.Lock()
        self.windows_emitted: int = 0

    def add(self, event: Dict[str, Any]):
        """Add a CEF event to the current window."""
        with self._lock:
            self.events.append(event)

    def check_window(self) -> Optional[List[Dict[str, Any]]]:
        """Check if window has closed. Returns events if so, else None."""
        now = time.time()
        if now - self.window_start >= self.window_sec:
            return self.flush()
        return None

    def flush(self) -> List[Dict[str, Any]]:
        """Close the current window and return its events."""
        with self._lock:
            window_events = list(self.events)

            # Keep overlap events for next window
            overlap_cutoff = time.time() - self.overlap_sec
            self.events = [
                e for e in self.events
                if self._parse_ts(e.get("timestamp", "")) > overlap_cutoff
            ]

            self.window_start = time.time()
            self.windows_emitted += 1

        return window_events

    @staticmethod
    def _parse_ts(ts: str) -> float:
        """Parse ISO timestamp to epoch. Falls back to current time."""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except (ValueError, AttributeError):
            return time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        with self._lock:
            return {
                "buffered_events": len(self.events),
                "window_age_sec": round(time.time() - self.window_start, 1),
                "windows_emitted": self.windows_emitted,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# Statistical Aggregator (Semantic Compression)
# ═══════════════════════════════════════════════════════════════════════════════

class StatisticalAggregator:
    """
    Compresses a window of CEF events into a statistical summary.

    The goal is to reduce ~3000 raw events in a 30-sec window into a
    ~500-800 token summary that any LLM can process, even with 8K context.
    """

    @staticmethod
    def aggregate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a window of events into a statistical summary."""
        if not events:
            return {"total_events": 0, "summary": "No events in window"}

        total = len(events)
        timestamps = [e.get("timestamp", "") for e in events]

        # ── Zone breakdown ──
        zone_counts = Counter(e.get("zone_id", "unknown") for e in events)

        # ── Event type breakdown ──
        type_counts = Counter(e.get("event_type", "unknown") for e in events)

        # ── Severity distribution ──
        severity_counts = Counter(e.get("severity", 0) for e in events)
        suspicious_count = sum(1 for e in events if e.get("suspicious", False))

        # ── Network traffic stats ──
        net_events = [e for e in events if e.get("event_class_id") == "NET"]
        net_stats = StatisticalAggregator._network_stats(net_events)

        # ── Device event stats ──
        dev_events = [e for e in events if e.get("event_class_id") in ("DEV", "PRC", "FSC", "FWC", "BHV")]
        dev_stats = StatisticalAggregator._device_stats(dev_events)

        # ── Sensor stats ──
        sensor_events = [e for e in events if e.get("event_class_id") == "SEN"]
        sensor_stats = StatisticalAggregator._sensor_stats(sensor_events)

        # ── Attack indicator summary ──
        attack_indicators = StatisticalAggregator._attack_indicators(events)

        return {
            "window_id": f"W{int(time.time())}",
            "window_start": min(timestamps) if timestamps else "",
            "window_end": max(timestamps) if timestamps else "",
            "total_events": total,
            "events_per_second": round(total / 30.0, 1),

            "zone_breakdown": dict(zone_counts.most_common()),
            "event_type_breakdown": dict(type_counts.most_common()),
            "severity_distribution": {str(k): v for k, v in sorted(severity_counts.items())},

            "suspicious_events": suspicious_count,
            "suspicious_pct": round(100.0 * suspicious_count / total, 1) if total else 0,

            "network_stats": net_stats,
            "device_stats": dev_stats,
            "sensor_stats": sensor_stats,
            "attack_indicators": attack_indicators,
        }

    @staticmethod
    def _network_stats(events: List[Dict]) -> Dict[str, Any]:
        """Compute network traffic statistics."""
        if not events:
            return {"count": 0}

        protocols = Counter(e.get("protocol", "?") for e in events)
        methods = Counter(e.get("method", "?") for e in events)
        status_codes = Counter(e.get("status_code", 0) for e in events)
        src_ips = Counter(e.get("src_ip", "") for e in events)
        dst_ports = Counter(e.get("dst_port", 0) for e in events)

        response_times = [e.get("response_time_ms", 0) for e in events if e.get("response_time_ms")]
        rps_values = [e.get("rps", 0) for e in events if e.get("rps", 0)]
        bytes_sent_total = sum(e.get("bytes_sent", 0) for e in events)
        bytes_recv_total = sum(e.get("bytes_received", 0) for e in events)

        # Error rate (4xx + 5xx)
        error_count = sum(1 for e in events if e.get("status_code", 200) >= 400)

        return {
            "count": len(events),
            "protocols": dict(protocols.most_common(5)),
            "methods": dict(methods.most_common(5)),
            "status_codes": dict(status_codes.most_common(5)),
            "unique_source_ips": len(src_ips),
            "top_source_ips": dict(src_ips.most_common(5)),
            "top_dst_ports": dict(dst_ports.most_common(5)),
            "avg_response_time_ms": round(sum(response_times) / len(response_times), 1) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "max_rps": max(rps_values) if rps_values else 0,
            "total_bytes_sent": bytes_sent_total,
            "total_bytes_received": bytes_recv_total,
            "error_rate_pct": round(100.0 * error_count / len(events), 1) if events else 0,
        }

    @staticmethod
    def _device_stats(events: List[Dict]) -> Dict[str, Any]:
        """Compute device event statistics."""
        if not events:
            return {"count": 0}

        subtypes = Counter(e.get("event_subtype", "unknown") for e in events)
        statuses = Counter(e.get("status", "unknown") for e in events)
        devices = Counter(e.get("device_id", "?") for e in events)

        return {
            "count": len(events),
            "subtypes": dict(subtypes.most_common(5)),
            "statuses": dict(statuses.most_common()),
            "unique_devices": len(devices),
            "compromised_count": sum(1 for e in events if e.get("status") == "compromised"),
        }

    @staticmethod
    def _sensor_stats(events: List[Dict]) -> Dict[str, Any]:
        """Compute sensor telemetry statistics."""
        if not events:
            return {"count": 0}

        lux_values = [e.get("ambient_lux", 0) for e in events]
        power_values = [e.get("power_watts", 0) for e in events]
        motion_count = sum(1 for e in events if e.get("motion_detected", False))

        return {
            "count": len(events),
            "avg_ambient_lux": round(sum(lux_values) / len(lux_values), 1) if lux_values else 0,
            "avg_power_watts": round(sum(power_values) / len(power_values), 1) if power_values else 0,
            "motion_detections": motion_count,
        }

    @staticmethod
    def _attack_indicators(events: List[Dict]) -> Dict[str, Any]:
        """Summarize attack indicators from suspicious events."""
        suspicious = [e for e in events if e.get("suspicious", False)]
        if not suspicious:
            return {"detected": False, "count": 0}

        indicator_types = Counter()
        mitre_ttps = set()
        stages = Counter()

        for e in suspicious:
            indicators = e.get("attack_indicators", {})
            if indicators:
                atype = indicators.get("type", "unknown")
                indicator_types[atype] += 1
                if "mitre_ttp" in indicators:
                    mitre_ttps.add(indicators["mitre_ttp"])
                if "stage" in indicators:
                    stages[indicators["stage"]] += 1

        return {
            "detected": True,
            "count": len(suspicious),
            "attack_types": dict(indicator_types.most_common()),
            "mitre_ttps": sorted(mitre_ttps),
            "stages": dict(stages.most_common()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Context Summary Generator (Token-Efficient)
# ═══════════════════════════════════════════════════════════════════════════════

class ContextSummaryGenerator:
    """
    Converts statistical aggregation into a concise natural language summary
    optimized for LLM consumption (~500-800 tokens).
    """

    @staticmethod
    def generate(stats: Dict[str, Any], previous_findings: str = "") -> str:
        """Generate LLM-ready context summary from aggregated stats."""
        lines = []

        # ── Header ──
        lines.append(f"=== SECURITY EVENT WINDOW: {stats.get('window_id', '?')} ===")
        lines.append(f"Period: {stats.get('window_start', '?')} to {stats.get('window_end', '?')}")
        lines.append(f"Total events: {stats.get('total_events', 0)} ({stats.get('events_per_second', 0)} events/sec)")
        lines.append("")

        # ── Zone Activity ──
        zones = stats.get("zone_breakdown", {})
        if zones:
            lines.append("ZONE ACTIVITY:")
            for zone, count in zones.items():
                lines.append(f"  {zone}: {count} events")
            lines.append("")

        # ── Suspicious Activity ──
        susp = stats.get("suspicious_events", 0)
        susp_pct = stats.get("suspicious_pct", 0)
        if susp > 0:
            lines.append(f"⚠ SUSPICIOUS EVENTS: {susp} ({susp_pct}% of total)")
            indicators = stats.get("attack_indicators", {})
            if indicators.get("detected"):
                types = indicators.get("attack_types", {})
                ttps = indicators.get("mitre_ttps", [])
                stages = indicators.get("stages", {})
                lines.append(f"  Attack types detected: {', '.join(f'{t}({c})' for t, c in types.items())}")
                if ttps:
                    lines.append(f"  MITRE ATT&CK TTPs: {', '.join(ttps)}")
                if stages:
                    lines.append(f"  Attack stages: {', '.join(f'{s}({c})' for s, c in stages.items())}")
            lines.append("")

        # ── Network Summary ──
        net = stats.get("network_stats", {})
        if net.get("count", 0) > 0:
            lines.append(f"NETWORK TRAFFIC ({net['count']} events):")
            lines.append(f"  Protocols: {net.get('protocols', {})}")
            lines.append(f"  Unique source IPs: {net.get('unique_source_ips', 0)}")
            if net.get("max_rps", 0) > 0:
                lines.append(f"  Max RPS observed: {net.get('max_rps', 0)}")
            lines.append(f"  Avg response time: {net.get('avg_response_time_ms', 0)}ms "
                         f"(max: {net.get('max_response_time_ms', 0)}ms)")
            lines.append(f"  Error rate: {net.get('error_rate_pct', 0)}%")
            lines.append(f"  Data volume: {net.get('total_bytes_sent', 0)}B sent, "
                         f"{net.get('total_bytes_received', 0)}B received")
            top_ips = net.get("top_source_ips", {})
            if top_ips:
                top_3 = list(top_ips.items())[:3]
                lines.append(f"  Top source IPs: {', '.join(f'{ip}({c})' for ip, c in top_3)}")
            lines.append("")

        # ── Device Summary ──
        dev = stats.get("device_stats", {})
        if dev.get("count", 0) > 0:
            lines.append(f"DEVICE EVENTS ({dev['count']} events):")
            lines.append(f"  Event subtypes: {dev.get('subtypes', {})}")
            lines.append(f"  Unique devices: {dev.get('unique_devices', 0)}")
            compromised = dev.get("compromised_count", 0)
            if compromised > 0:
                lines.append(f"  ⚠ COMPROMISED DEVICES: {compromised}")
            lines.append("")

        # ── Sensor Summary ──
        sensor = stats.get("sensor_stats", {})
        if sensor.get("count", 0) > 0:
            lines.append(f"SENSOR DATA ({sensor['count']} readings):")
            lines.append(f"  Avg ambient: {sensor.get('avg_ambient_lux', 0)} lux, "
                         f"Avg power: {sensor.get('avg_power_watts', 0)}W, "
                         f"Motion detections: {sensor.get('motion_detections', 0)}")
            lines.append("")

        # ── Severity Distribution ──
        sev = stats.get("severity_distribution", {})
        if sev:
            lines.append(f"SEVERITY DISTRIBUTION: {sev}")
            lines.append("")

        # ── Previous Findings (Context Condensation) ──
        if previous_findings:
            lines.append(f"PREVIOUS WINDOW FINDINGS:")
            lines.append(f"  {previous_findings}")
            lines.append("")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph Agent State & Workflow
# ═══════════════════════════════════════════════════════════════════════════════

class LogIngestionState(BaseModel):
    """State for the Log Ingestion Agent LangGraph workflow."""
    messages: list = []
    raw_events: list = []
    cef_events: list = []
    aggregated_stats: Dict[str, Any] = {}
    context_summary: str = ""
    previous_findings: str = ""
    window_id: str = ""
    events_processed: int = 0
    suspicious_detected: bool = False


class LogIngestionAgent:
    """
    LangGraph agent for Tier 1 SOC log ingestion.

    Workflow: Collect → Normalize → Aggregate → Summarize → Publish
    """

    def __init__(self, kafka_servers: str = "localhost:19092"):
        self.kafka_servers = kafka_servers
        self.normalizer = CEFNormalizer()
        self.buffer = SlidingWindowBuffer(window_sec=30.0, overlap_sec=10.0)
        self.aggregator = StatisticalAggregator()
        self.summary_gen = ContextSummaryGenerator()
        self.graph = self._create_graph()

        self.consumer: Optional[Any] = None
        self.producer: Optional[Any] = None
        self.running = False
        self.previous_findings = ""
        self.total_processed = 0
        self.total_windows = 0

    def _create_graph(self):
        """Create LangGraph workflow for log ingestion."""
        workflow = StateGraph(LogIngestionState)

        workflow.add_node("normalize_events", self._normalize_events)
        workflow.add_node("aggregate_stats", self._aggregate_stats)
        workflow.add_node("generate_summary", self._generate_summary)

        workflow.set_entry_point("normalize_events")
        workflow.add_edge("normalize_events", "aggregate_stats")
        workflow.add_edge("aggregate_stats", "generate_summary")
        workflow.add_edge("generate_summary", END)

        return workflow.compile()

    def _normalize_events(self, state: LogIngestionState) -> dict:
        """Stage 2a: Normalize raw events to CEF format."""
        cef_events = []
        for raw in state.raw_events:
            try:
                cef = self.normalizer.normalize(raw)
                cef_events.append(cef)
            except Exception as e:
                logger.warning(f"Failed to normalize event: {e}")

        suspicious = any(e.get("suspicious", False) for e in cef_events)

        return {
            "cef_events": cef_events,
            "events_processed": len(cef_events),
            "suspicious_detected": suspicious,
        }

    def _aggregate_stats(self, state: LogIngestionState) -> dict:
        """Stage 2b: Statistical aggregation (semantic compression)."""
        stats = self.aggregator.aggregate(state.cef_events)
        return {"aggregated_stats": stats, "window_id": stats.get("window_id", "")}

    def _generate_summary(self, state: LogIngestionState) -> dict:
        """Stage 3: Generate LLM-ready context summary."""
        summary = self.summary_gen.generate(
            state.aggregated_stats,
            previous_findings=state.previous_findings,
        )
        return {"context_summary": summary}

    def process_window(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a window of raw events through the full pipeline.

        Args:
            raw_events: List of raw events from Kafka

        Returns:
            Dict with context_summary, aggregated_stats, and metadata
        """
        initial_state = LogIngestionState(
            raw_events=raw_events,
            previous_findings=self.previous_findings,
        )

        result = self.graph.invoke(initial_state)

        # Update context condensation for next window
        stats = result.get("aggregated_stats", {})
        suspicious = stats.get("suspicious_events", 0)
        if suspicious > 0:
            indicators = stats.get("attack_indicators", {})
            types = indicators.get("attack_types", {})
            self.previous_findings = (
                f"Previous window had {suspicious} suspicious events. "
                f"Types: {types}. "
                f"Total events: {stats.get('total_events', 0)}."
            )
        else:
            self.previous_findings = (
                f"Previous window: {stats.get('total_events', 0)} events, "
                f"no suspicious activity detected."
            )

        self.total_processed += len(raw_events)
        self.total_windows += 1

        return {
            "window_id": result.get("window_id", ""),
            "context_summary": result.get("context_summary", ""),
            "aggregated_stats": stats,
            "events_processed": len(raw_events),
            "suspicious_detected": result.get("suspicious_detected", False),
        }

    # ── Kafka Streaming Mode ──────────────────────────────────────────────

    def _connect_kafka(self):
        """Connect to Kafka consumer and producer."""
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka not available — run in direct mode with process_window()")
            return

        try:
            self.consumer = KafkaConsumer(
                "network_events", "device_events", "sensor_data",
                bootstrap_servers=self.kafka_servers,
                group_id="log_ingestion_agent",
                auto_offset_reset="latest",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                consumer_timeout_ms=1000,
            )
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            logger.info(f"Connected to Kafka at {self.kafka_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")

    def _publish_summary(self, result: Dict[str, Any]):
        """Publish processed summary to normalized_events topic."""
        if self.producer:
            try:
                self.producer.send("normalized_events", value=result)
            except Exception as e:
                logger.error(f"Failed to publish summary: {e}")
        else:
            logger.info(f"[normalized_events] Window {result.get('window_id')}: "
                        f"{result.get('events_processed', 0)} events → "
                        f"{len(result.get('context_summary', ''))} chars summary")

    def run(self):
        """
        Run in streaming mode: consume from Kafka, buffer, process windows.

        This is the main loop for production use inside Docker.
        """
        self._connect_kafka()
        self.running = True
        logger.info("Log Ingestion Agent starting in streaming mode...")

        while self.running:
            try:
                # Poll Kafka for events
                if self.consumer:
                    records = self.consumer.poll(timeout_ms=500)
                    for topic_partition, messages in records.items():
                        for msg in messages:
                            cef = self.normalizer.normalize(msg.value)
                            self.buffer.add(cef)

                # Check if window has closed
                window_events = self.buffer.check_window()
                if window_events:
                    logger.info(
                        f"Processing window: {len(window_events)} events"
                    )
                    result = self.process_window(
                        [e for e in window_events]  # Raw events already CEF
                    )
                    self._publish_summary(result)

                    logger.info(
                        f"Window {result.get('window_id')}: "
                        f"processed={result.get('events_processed', 0)}, "
                        f"suspicious={result.get('suspicious_detected', False)}, "
                        f"summary_len={len(result.get('context_summary', ''))} chars"
                    )

                time.sleep(0.1)

            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                logger.error(f"Processing error: {e}")
                time.sleep(1)

        logger.info(
            f"Log Ingestion Agent stopped. "
            f"Total: {self.total_processed} events, {self.total_windows} windows"
        )

    def stop(self):
        """Stop the streaming loop."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "running": self.running,
            "total_processed": self.total_processed,
            "total_windows": self.total_windows,
            "buffer": self.buffer.get_stats(),
            "previous_findings": self.previous_findings,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI & Demo Mode
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Run a demo processing a synthetic batch of events."""
    import random

    agent = LogIngestionAgent()

    # Generate synthetic events (mix of normal + suspicious)
    events = []
    zones = ["bkc_commercial", "reliance_hospital", "airport"]

    # Normal traffic
    for i in range(50):
        zone = random.choice(zones)
        events.append({
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone,
            "device_id": f"{zone}_pole_{i % 10:03d}",
            "source_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "destination_ip": "10.0.0.1",
            "destination_port": random.choice([80, 443, 1883]),
            "protocol": random.choice(["HTTP", "HTTPS", "MQTT"]),
            "method": "GET",
            "endpoint": "/api/v1/lights/status",
            "status_code": 200,
            "response_time_ms": round(random.gauss(50, 15), 1),
            "bytes_sent": random.randint(100, 2000),
            "bytes_received": random.randint(200, 5000),
        })

    # Some suspicious traffic (HTTP flood indicators)
    for i in range(15):
        events.append({
            "event_type": "network_traffic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": "bkc_commercial",
            "device_id": f"bkc_commercial_pole_{i % 5:03d}",
            "source_ip": f"{random.randint(45,220)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "destination_ip": "10.1.1.1",
            "destination_port": 80,
            "protocol": "HTTP",
            "method": "GET",
            "endpoint": "/api/v1/lights/status",
            "status_code": random.choice([200, 429, 503]),
            "response_time_ms": round(random.uniform(500, 3000), 1),
            "bytes_sent": random.randint(50, 500),
            "bytes_received": random.randint(0, 200),
            "requests_per_second": random.randint(300, 800),
            "suspicious": True,
            "attack_indicators": {
                "type": "http_flood",
                "rps_spike": True,
                "distributed_sources": True,
            },
        })

    # Sensor data
    for i in range(20):
        events.append({
            "event_type": "sensor_telemetry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": random.choice(zones),
            "device_id": f"{random.choice(zones)}_pole_{i % 8:03d}",
            "metrics": {
                "ambient_lux": round(random.uniform(0, 500), 2),
                "brightness_pct": random.randint(10, 100),
                "power_watts": round(random.uniform(50, 250), 2),
                "motion_detected": random.random() < 0.3,
                "temperature_c": round(random.gauss(28, 3), 1),
            },
        })

    # Process through the pipeline
    result = agent.process_window(events)

    print(f"\n{'='*70}")
    print(f"  LOG INGESTION AGENT — Demo Results")
    print(f"{'='*70}")
    print(f"  Events processed: {result['events_processed']}")
    print(f"  Suspicious detected: {result['suspicious_detected']}")
    print(f"  Summary length: {len(result['context_summary'])} chars")
    print(f"  Estimated tokens: ~{len(result['context_summary']) // 4}")
    print(f"\n{'─'*70}")
    print(f"  CONTEXT SUMMARY (sent to downstream agents):")
    print(f"{'─'*70}")
    print(result["context_summary"])
    print(f"{'='*70}\n")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Log Ingestion Agent")
    parser.add_argument("--mode", choices=["stream", "demo"], default="demo")
    parser.add_argument("--kafka", default="localhost:19092")
    args = parser.parse_args()

    if args.mode == "demo":
        demo()
    else:
        agent = LogIngestionAgent(kafka_servers=args.kafka)
        try:
            agent.run()
        except KeyboardInterrupt:
            agent.stop()
