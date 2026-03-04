"""
Live Pipeline — Kafka-consuming SOC pipeline service for Docker Arena.

Runs inside the soc-agents container. Continuously consumes events from
Kafka topics, buffers them into time-based windows, runs the 6-agent
SOCPipeline on each window, and publishes results to Redis + Kafka.

Architecture:
    Kafka (network_events, device_events, sensor_data, cyber_alerts)
        ↓   consume + buffer (30s windows)
    SOCPipeline.execute(buffered_events)
        ↓   results
    Redis (arena:latest_result, arena:detection_log)
    Kafka (incident_reports topic)

Model Swapping:
    Reads `arena:active_model` from Redis before each window evaluation.
    If the model changed since last window, re-initializes SOCPipeline
    with the new model via ModelRegistry.
"""

import os
import sys
import json
import time
import signal
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

# ── Logging ──
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("live-pipeline")

# ── Kafka ──
try:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed — live pipeline requires Kafka")

# ── Redis ──
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not installed — results will not be stored in Redis")

# ── SOC Pipeline ──
# Add cybersecurity src to path for imports
AGENT_SRC = os.path.join(os.path.dirname(__file__), "..", "agents", "cybersecurity", "src")
if os.path.isdir(AGENT_SRC):
    sys.path.insert(0, AGENT_SRC)

try:
    from graph.cybersecurity_graph import SOCPipeline
    SOC_AVAILABLE = True
except ImportError:
    SOC_AVAILABLE = False
    logger.warning("SOCPipeline not available — running in log-only mode")

try:
    from arena.model_registry import ModelRegistry
except ImportError:
    try:
        from model_registry import ModelRegistry
    except ImportError:
        ModelRegistry = None


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WINDOW_SECONDS = int(os.getenv("PIPELINE_WINDOW_SECONDS", "30"))
ACTIVE_MODEL = os.getenv("ACTIVE_MODEL", "llama-3.1-8b")

CONSUME_TOPICS = [
    "network_events",
    "device_events",
    "sensor_data",
    "cyber_alerts",
]

RESULT_TOPIC = "incident_reports"

# Redis keys
REDIS_ACTIVE_MODEL = "arena:active_model"
REDIS_LATEST_RESULT = "arena:latest_result"          # latest pipeline output
REDIS_DETECTION_LOG = "arena:detection_log"           # list of all detections
REDIS_PIPELINE_STATUS = "arena:pipeline_status"       # running/stopped


# ═══════════════════════════════════════════════════════════════════════════════
# Live Pipeline Service
# ═══════════════════════════════════════════════════════════════════════════════

class LivePipeline:
    """
    Kafka → Buffer → SOCPipeline → Redis/Kafka results publisher.

    Runs continuously inside a Docker container. Each WINDOW_SECONDS interval:
      1. Flush the event buffer
      2. Read active model from Redis
      3. Run SOCPipeline.execute(events)
      4. Publish results to Redis + Kafka incident_reports
    """

    def __init__(self):
        self.running = False
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = threading.Lock()
        self.window_count = 0
        self.total_events_processed = 0

        # ── Kafka ──
        self.consumer: Optional[KafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None

        # ── Redis ──
        self.redis_client = None

        # ── SOC Pipeline ──
        self.pipeline: Optional[Any] = None
        self.current_model_id = ACTIVE_MODEL

        # Stats
        self.stats = {
            "windows_processed": 0,
            "events_consumed": 0,
            "detections": 0,
            "errors": 0,
            "start_time": None,
        }

    # ── Initialization ─────────────────────────────────────────────────────

    def _connect_kafka(self):
        """Connect to Kafka with retry logic."""
        for attempt in range(1, 11):
            try:
                self.consumer = KafkaConsumer(
                    *CONSUME_TOPICS,
                    bootstrap_servers=KAFKA_SERVERS,
                    group_id="soc_live_pipeline",
                    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                    key_deserializer=lambda x: x.decode("utf-8") if x else None,
                    auto_offset_reset="latest",
                    enable_auto_commit=True,
                    consumer_timeout_ms=1000,
                    max_poll_records=200,
                )
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_SERVERS,
                    value_serializer=lambda x: json.dumps(x, default=str).encode("utf-8"),
                    key_serializer=lambda x: x.encode("utf-8") if x else None,
                )
                logger.info(
                    f"Kafka connected (attempt {attempt}). "
                    f"Consuming: {CONSUME_TOPICS} → Producing: {RESULT_TOPIC}"
                )
                return
            except Exception as e:
                logger.warning(f"Kafka connection attempt {attempt}/10 failed: {e}")
                time.sleep(min(attempt * 2, 15))

        raise ConnectionError("Failed to connect to Kafka after 10 attempts")

    def _connect_redis(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available — results will only go to Kafka")
            return

        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Redis connected: {REDIS_URL}")

            # Set initial model
            existing = self.redis_client.get(REDIS_ACTIVE_MODEL)
            if existing:
                self.current_model_id = existing
                logger.info(f"Active model from Redis: {self.current_model_id}")
            else:
                self.redis_client.set(REDIS_ACTIVE_MODEL, self.current_model_id)
                logger.info(f"Active model set to default: {self.current_model_id}")

            # Set pipeline status
            self.redis_client.set(REDIS_PIPELINE_STATUS, "starting")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} — continuing without Redis")
            self.redis_client = None

    def _init_pipeline(self, model_id: str = None):
        """Initialize or re-initialize the SOC pipeline with a model."""
        if not SOC_AVAILABLE:
            logger.info("SOCPipeline not available — running in passthrough mode")
            return

        model_id = model_id or self.current_model_id
        try:
            registry = ModelRegistry() if ModelRegistry else None
            self.pipeline = SOCPipeline(model_registry=registry)
            self.current_model_id = model_id
            logger.info(f"SOCPipeline initialized with model: {model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize SOCPipeline: {e}")
            self.pipeline = None

    # ── Consumer Loop ──────────────────────────────────────────────────────

    def _consume_loop(self):
        """Background thread: poll Kafka and buffer events."""
        logger.info("Consumer thread started")
        while self.running:
            try:
                batch = self.consumer.poll(timeout_ms=1000)
                if not batch:
                    continue

                new_events = []
                for tp, messages in batch.items():
                    for msg in messages:
                        if isinstance(msg.value, dict):
                            # Add Kafka metadata
                            msg.value["_kafka_meta"] = {
                                "topic": tp.topic,
                                "partition": tp.partition,
                                "offset": msg.offset,
                                "timestamp": msg.timestamp,
                            }
                            new_events.append(msg.value)

                if new_events:
                    with self.buffer_lock:
                        self.event_buffer.extend(new_events)
                    self.stats["events_consumed"] += len(new_events)
                    logger.debug(f"Buffered {len(new_events)} events (total buffer: {len(self.event_buffer)})")

            except KafkaError as e:
                logger.error(f"Kafka consumer error: {e}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                time.sleep(1)

        logger.info("Consumer thread stopped")

    # ── Window Processor ───────────────────────────────────────────────────

    def _check_model_swap(self):
        """Check Redis for model swap request."""
        if not self.redis_client:
            return

        try:
            requested = self.redis_client.get(REDIS_ACTIVE_MODEL)
            if requested and requested != self.current_model_id:
                logger.info(f"Model swap requested: {self.current_model_id} → {requested}")
                self._init_pipeline(requested)
        except Exception as e:
            logger.warning(f"Error checking model swap: {e}")

    def _process_window(self):
        """Flush buffer and run SOCPipeline on the window."""
        # Flush buffer atomically
        with self.buffer_lock:
            events = list(self.event_buffer)
            self.event_buffer.clear()

        if not events:
            logger.debug("Empty window — skipping pipeline")
            return

        self.window_count += 1
        window_id = f"w{self.window_count}_{datetime.now(timezone.utc).strftime('%H%M%S')}"

        logger.info(
            f"\n{'─'*60}\n"
            f"  WINDOW {self.window_count}: {len(events)} events\n"
            f"  Model: {self.current_model_id}\n"
            f"{'─'*60}"
        )

        # Check for model swap before processing
        self._check_model_swap()

        # Run SOC Pipeline
        result = self._run_pipeline(events, window_id)

        # Publish results
        self._publish_result(result, window_id)

        self.total_events_processed += len(events)
        self.stats["windows_processed"] += 1

    def _run_pipeline(self, events: List[Dict], window_id: str) -> Dict[str, Any]:
        """Run the SOC pipeline on a batch of events."""
        start = time.time()

        if not self.pipeline:
            # Passthrough mode — just summarize events
            event_types = defaultdict(int)
            for e in events:
                event_types[e.get("event_type", "unknown")] += 1

            return {
                "window_id": window_id,
                "mode": "passthrough",
                "model_id": self.current_model_id,
                "total_events": len(events),
                "event_types": dict(event_types),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline_status": "passthrough",
                "risk_level": "unknown",
                "detection_results": {},
                "processing_time_sec": round(time.time() - start, 3),
            }

        try:
            # Build scenario_config for the pipeline
            scenario_config = {
                "scenario_id": "live",
                "model_id": self.current_model_id,
                "window_id": window_id,
                "window_size": len(events),
            }

            pipeline_result = self.pipeline.execute(
                raw_events=events,
                scenario_config=scenario_config,
            )

            elapsed = round(time.time() - start, 3)

            # Check for detections
            detection = pipeline_result.get("detection_results", {})
            risk = pipeline_result.get("risk_level", "none")
            if risk in ("high", "critical"):
                self.stats["detections"] += 1

            result = {
                "window_id": window_id,
                "mode": "live",
                "model_id": self.current_model_id,
                "total_events": len(events),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time_sec": elapsed,
                **pipeline_result,
            }

            logger.info(
                f"  Pipeline complete: risk={risk} "
                f"elapsed={elapsed}s events={len(events)}"
            )
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Pipeline execution error: {e}")
            return {
                "window_id": window_id,
                "mode": "live",
                "model_id": self.current_model_id,
                "total_events": len(events),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline_status": "error",
                "risk_level": "unknown",
                "error": str(e),
                "processing_time_sec": round(time.time() - start, 3),
            }

    # ── Result Publishing ──────────────────────────────────────────────────

    def _publish_result(self, result: Dict[str, Any], window_id: str):
        """Publish pipeline result to Kafka + Redis."""
        # Kafka: incident_reports topic
        try:
            self.producer.send(
                RESULT_TOPIC,
                key=window_id,
                value=result,
            )
            self.producer.flush(timeout=5)
            logger.debug(f"Result published to Kafka topic: {RESULT_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to publish result to Kafka: {e}")

        # Redis: latest result + detection log
        if self.redis_client:
            try:
                result_json = json.dumps(result, default=str)
                self.redis_client.set(REDIS_LATEST_RESULT, result_json)

                # Append to detection log (capped list)
                self.redis_client.lpush(REDIS_DETECTION_LOG, result_json)
                self.redis_client.ltrim(REDIS_DETECTION_LOG, 0, 499)  # Keep last 500

                # Update stats
                self.redis_client.hset("arena:stats", mapping={
                    "windows_processed": str(self.stats["windows_processed"]),
                    "events_consumed": str(self.stats["events_consumed"]),
                    "detections": str(self.stats["detections"]),
                    "errors": str(self.stats["errors"]),
                    "current_model": self.current_model_id,
                    "last_window": window_id,
                    "last_update": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.error(f"Failed to publish result to Redis: {e}")

    # ── Main Run Loop ──────────────────────────────────────────────────────

    def start(self):
        """Start the live pipeline service."""
        logger.info(
            f"\n{'═'*60}\n"
            f"  AI CYBER ARENA — Live Pipeline\n"
            f"  Kafka:   {KAFKA_SERVERS}\n"
            f"  Redis:   {REDIS_URL}\n"
            f"  Window:  {WINDOW_SECONDS}s\n"
            f"  Model:   {ACTIVE_MODEL}\n"
            f"  Topics:  {CONSUME_TOPICS}\n"
            f"{'═'*60}\n"
        )

        self.stats["start_time"] = datetime.now(timezone.utc).isoformat()

        # 1. Connect to services
        self._connect_kafka()
        self._connect_redis()
        self._init_pipeline()

        # 2. Start consumer thread
        self.running = True
        consumer_thread = threading.Thread(target=self._consume_loop, daemon=True)
        consumer_thread.start()

        # Update Redis status
        if self.redis_client:
            self.redis_client.set(REDIS_PIPELINE_STATUS, "running")

        logger.info("Live pipeline running. Press Ctrl+C to stop.")

        # 3. Window processing loop (main thread)
        try:
            while self.running:
                time.sleep(WINDOW_SECONDS)
                if self.running:
                    self._process_window()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self):
        """Gracefully stop the pipeline."""
        logger.info("Stopping live pipeline...")
        self.running = False

        # Process any remaining events
        if self.event_buffer:
            logger.info(f"Processing {len(self.event_buffer)} remaining events...")
            self._process_window()

        # Close connections
        if self.consumer:
            try:
                self.consumer.close()
            except Exception:
                pass

        if self.producer:
            try:
                self.producer.flush(timeout=5)
                self.producer.close()
            except Exception:
                pass

        if self.redis_client:
            try:
                self.redis_client.set(REDIS_PIPELINE_STATUS, "stopped")
            except Exception:
                pass

        logger.info(
            f"\n{'═'*60}\n"
            f"  Live Pipeline Stopped\n"
            f"  Windows: {self.stats['windows_processed']}\n"
            f"  Events:  {self.stats['events_consumed']}\n"
            f"  Detections: {self.stats['detections']}\n"
            f"  Errors:  {self.stats['errors']}\n"
            f"{'═'*60}\n"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    pipeline = LivePipeline()

    def signal_handler(sig, frame):
        pipeline.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    pipeline.start()


if __name__ == "__main__":
    main()
