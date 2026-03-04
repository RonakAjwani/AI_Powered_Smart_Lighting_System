"""
Log Viewer Server — Wireshark-style real-time grid event viewer.

Provides:
  - WebSocket server streaming live Kafka events
  - REST API for querying historical events
  - Serves the static HTML/JS/CSS viewer UI

Usage:
  python -m arena.log_viewer
  Then open http://localhost:8888 in browser
"""

import os
import sys
import json
import asyncio
import logging
import signal
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional
from collections import deque

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("log-viewer")

try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

try:
    import websockets
    from websockets.server import serve as ws_serve
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


# ── Event Buffer ───────────────────────────────────────────

class EventBuffer:
    """Thread-safe circular buffer for recent events."""

    def __init__(self, maxlen: int = 10000):
        self.events: deque = deque(maxlen=maxlen)
        self.event_id_counter: int = 0
        self.stats: Dict[str, int] = {
            "total_events": 0,
            "network_events": 0,
            "device_events": 0,
            "sensor_events": 0,
            "alert_events": 0,
        }

    def add(self, topic: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Add event to buffer and assign sequential ID."""
        self.event_id_counter += 1
        enriched = {
            "id": self.event_id_counter,
            "topic": topic,
            "received_at": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        self.events.append(enriched)
        self.stats["total_events"] += 1

        etype = event.get("event_type", "unknown")
        if "network" in etype:
            self.stats["network_events"] += 1
        elif "device" in etype:
            self.stats["device_events"] += 1
        elif "sensor" in etype:
            self.stats["sensor_events"] += 1
        elif "alert" in etype:
            self.stats["alert_events"] += 1

        return enriched

    def get_recent(self, count: int = 100) -> list:
        """Get most recent N events."""
        items = list(self.events)
        return items[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {**self.stats, "buffer_size": len(self.events)}


# ── Kafka Consumer (Background Thread) ────────────────────

class KafkaEventStream:
    """Streams events from Kafka topics into the buffer."""

    def __init__(self, buffer: EventBuffer, servers: str):
        self.buffer = buffer
        self.servers = servers
        self.topics = [
            "network_events", "device_events", "sensor_data",
            "cyber_alerts", "normalized_events", "incident_reports",
        ]
        self.running = False

    async def stream(self, ws_clients: Set):
        """Poll Kafka and push events to buffer + WebSocket clients."""
        if not KAFKA_AVAILABLE:
            logger.warning("kafka-python not installed, using demo data")
            await self._stream_demo(ws_clients)
            return

        try:
            consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.servers,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                group_id="log-viewer",
                consumer_timeout_ms=500,
            )
            logger.info(f"Connected to Kafka at {self.servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}, using demo data")
            await self._stream_demo(ws_clients)
            return

        self.running = True
        while self.running:
            try:
                records = consumer.poll(timeout_ms=200)
                for topic_partition, messages in records.items():
                    topic = topic_partition.topic
                    for msg in messages:
                        enriched = self.buffer.add(topic, msg.value)
                        payload = json.dumps(enriched, default=str)
                        disconnected = set()
                        for ws in ws_clients.copy():
                            try:
                                await ws.send(payload)
                            except Exception:
                                disconnected.add(ws)
                        ws_clients -= disconnected
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Kafka stream error: {e}")
                await asyncio.sleep(1)

        consumer.close()

    async def _stream_demo(self, ws_clients: Set):
        """Generate demo events for testing without Kafka."""
        import random

        zones = ["bkc_commercial", "reliance_hospital", "airport", "port_area",
                 "school_complex", "residential", "highway_corridor"]
        self.running = True
        logger.info("Running in DEMO mode with simulated events")

        while self.running:
            zone = random.choice(zones)
            event_type = random.choices(
                ["network_traffic", "sensor_telemetry", "device_event"],
                weights=[6, 3, 1]
            )[0]

            if event_type == "network_traffic":
                event = {
                    "event_type": "network_traffic",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "zone_id": zone,
                    "source_ip": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
                    "destination_ip": "10.0.0.1",
                    "destination_port": random.choice([80, 443, 1883, 5683]),
                    "protocol": random.choice(["HTTP", "HTTPS", "MQTT", "CoAP"]),
                    "method": random.choice(["GET", "POST", "PUT"]),
                    "endpoint": random.choice([
                        "/api/v1/lights/status", "/api/v1/sensors/ambient",
                        "/api/v1/health", "/api/v1/firmware/check",
                    ]),
                    "status_code": random.choice([200, 200, 200, 201, 304, 400, 500]),
                    "response_time_ms": round(random.gauss(50, 15), 1),
                    "bytes_sent": random.randint(100, 2000),
                    "bytes_received": random.randint(200, 5000),
                    "packet_size": random.randint(200, 1500),
                    "device_id": f"{zone}_pole_{random.randint(0,20):03d}",
                }
                topic = "network_events"
            elif event_type == "sensor_telemetry":
                event = {
                    "event_type": "sensor_telemetry",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "zone_id": zone,
                    "device_id": f"{zone}_pole_{random.randint(0,20):03d}",
                    "device_type": "smart_pole",
                    "metrics": {
                        "ambient_lux": round(random.uniform(0, 500), 2),
                        "brightness_pct": random.randint(10, 100),
                        "power_watts": round(random.uniform(50, 250), 2),
                        "motion_detected": random.random() < 0.3,
                        "temperature_c": round(random.gauss(28, 3), 1),
                    },
                }
                topic = "sensor_data"
            else:
                event = {
                    "event_type": "device_event",
                    "event_subtype": random.choice(["heartbeat", "config_sync", "firmware_check"]),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "zone_id": zone,
                    "device_id": f"{zone}_pole_{random.randint(0,20):03d}",
                    "status": "online",
                }
                topic = "device_events"

            enriched = self.buffer.add(topic, event)
            payload = json.dumps(enriched, default=str)
            disconnected = set()
            for ws in ws_clients.copy():
                try:
                    await ws.send(payload)
                except Exception:
                    disconnected.add(ws)
            ws_clients -= disconnected

            await asyncio.sleep(random.uniform(0.05, 0.3))

    def stop(self):
        self.running = False


# ── HTTP + WebSocket Server ────────────────────────────────

HTML_PATH = os.path.join(os.path.dirname(__file__), "log_viewer.html")


async def run_server():
    """Start the log viewer server."""
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    port = int(os.getenv("LOG_VIEWER_PORT", "8888"))

    buffer = EventBuffer(maxlen=10000)
    kafka_stream = KafkaEventStream(buffer, servers)
    ws_clients: Set = set()

    # ── WebSocket Handler ──
    async def ws_handler(websocket):
        ws_clients.add(websocket)
        logger.info(f"WebSocket client connected ({len(ws_clients)} total)")
        try:
            # Send recent events on connect
            recent = buffer.get_recent(200)
            for event in recent:
                await websocket.send(json.dumps(event, default=str))
            # Keep alive
            async for msg in websocket:
                # Handle filter requests from client
                try:
                    data = json.loads(msg)
                    if data.get("type") == "get_stats":
                        await websocket.send(json.dumps({
                            "type": "stats",
                            "data": buffer.get_stats()
                        }))
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            ws_clients.discard(websocket)
            logger.info(f"WebSocket client disconnected ({len(ws_clients)} remaining)")

    # ── HTTP Handler (serves the HTML viewer) ──
    async def http_handler(request):
        if request.path == "/" or request.path == "/index.html":
            try:
                with open(HTML_PATH, "r", encoding="utf-8") as f:
                    html = f.read()
                return web.Response(text=html, content_type="text/html")
            except FileNotFoundError:
                return web.Response(text="log_viewer.html not found", status=404)
        elif request.path == "/api/stats":
            return web.json_response(buffer.get_stats())
        elif request.path == "/api/events":
            count = int(request.query.get("count", "100"))
            return web.json_response(buffer.get_recent(count), default=str)
        else:
            return web.Response(text="Not found", status=404)

    # ── Start Everything ──
    if not AIOHTTP_AVAILABLE or not WS_AVAILABLE:
        logger.error("aiohttp and websockets are required. Install with: pip install aiohttp websockets")
        return

    # HTTP server
    app = web.Application()
    app.router.add_get("/", http_handler)
    app.router.add_get("/index.html", http_handler)
    app.router.add_get("/api/stats", http_handler)
    app.router.add_get("/api/events", http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # WebSocket server
    ws_server = await ws_serve(ws_handler, "0.0.0.0", port + 1)

    logger.info(f"=" * 60)
    logger.info(f"  Log Viewer running!")
    logger.info(f"  Web UI:    http://localhost:{port}")
    logger.info(f"  WebSocket: ws://localhost:{port + 1}")
    logger.info(f"=" * 60)

    # Kafka consumer
    kafka_task = asyncio.create_task(kafka_stream.stream(ws_clients))

    # Wait for shutdown
    stop_event = asyncio.Event()

    def handle_signal():
        kafka_stream.stop()
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass  # Windows doesn't support add_signal_handler

    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        kafka_stream.stop()

    kafka_task.cancel()
    ws_server.close()
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(run_server())
