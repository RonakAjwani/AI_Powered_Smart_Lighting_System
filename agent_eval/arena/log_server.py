"""
Log Server — Bridges Kafka events to the Arena Log Viewer UI via WebSocket.

Consumes from all Kafka topics (network_events, device_events, sensor_data,
cyber_alerts) and streams them live to connected WebSocket clients.
Also serves the log_viewer.html file on HTTP.

Usage:
    python -m arena.log_server                     # defaults: 8888 (HTTP) + 8889 (WS)
    python -m arena.log_server --port 9000         # custom HTTP port (WS = port+1)
    python -m arena.log_server --kafka localhost:19092
"""

import os
import sys
import json
import time
import asyncio
import logging
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("log-server")

# ── Dependencies ──
try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False
    logger.warning("websockets not installed — run: pip install websockets")

try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed — run: pip install kafka-python")

# ── Config ──
KAFKA_TOPICS = ["network_events", "device_events", "sensor_data", "cyber_alerts"]
HTML_FILE = Path(__file__).parent / "log_viewer.html"


class LogServer:
    """Bridges Kafka → WebSocket for the Arena Log Viewer."""

    def __init__(
        self,
        kafka_servers: str = "localhost:19092",
        http_port: int = 8888,
        ws_port: int = 8889,
    ):
        self.kafka_servers = kafka_servers
        self.http_port = http_port
        self.ws_port = ws_port
        self.clients: set = set()
        self.event_count = 0
        self.running = False
        self._event_buffer: list = []  # Buffer recent events for new clients

    async def ws_handler(self, websocket):
        """Handle a new WebSocket client connection."""
        self.clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id} (total: {len(self.clients)})")

        # Send buffered events to catch up
        for event in self._event_buffer[-100:]:
            try:
                await websocket.send(event)
            except Exception:
                break

        try:
            async for _ in websocket:
                pass  # Keep connection alive, we only push
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected: {client_id} (total: {len(self.clients)})")

    async def broadcast(self, message: str):
        """Send a message to all connected WebSocket clients."""
        if not self.clients:
            return
        disconnected = set()
        for client in set(self.clients):  # iterate over a snapshot copy
            try:
                await client.send(message)
            except Exception:
                disconnected.add(client)
        self.clients -= disconnected

    def _kafka_consumer_thread(self, loop: asyncio.AbstractEventLoop):
        """Background thread: consume Kafka events and broadcast via WebSocket."""
        if not KAFKA_AVAILABLE:
            logger.error("Kafka not available — using simulated events")
            self._simulate_events_thread(loop)
            return

        try:
            consumer = KafkaConsumer(
                *KAFKA_TOPICS,
                bootstrap_servers=self.kafka_servers.split(","),
                group_id="log_viewer_server",
                auto_offset_reset="latest",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                consumer_timeout_ms=1000,
            )
            logger.info(f"Kafka consumer started: {', '.join(KAFKA_TOPICS)}")
        except Exception as e:
            logger.error(f"Kafka connection failed: {e} — falling back to simulation")
            self._simulate_events_thread(loop)
            return

        while self.running:
            try:
                messages = consumer.poll(timeout_ms=500)
                for tp, records in messages.items():
                    for record in records:
                        self.event_count += 1
                        event = record.value
                        event["_topic"] = record.topic
                        event["_offset"] = record.offset
                        event["_partition"] = record.partition

                        # Assign sequential ID if missing
                        if "id" not in event:
                            event["id"] = self.event_count

                        msg = json.dumps(event)
                        self._event_buffer.append(msg)

                        # Keep buffer bounded
                        if len(self._event_buffer) > 5000:
                            self._event_buffer = self._event_buffer[-3000:]

                        asyncio.run_coroutine_threadsafe(
                            self.broadcast(msg), loop
                        )
            except Exception as e:
                logger.warning(f"Kafka poll error: {e}")
                time.sleep(1)

        consumer.close()

    def _simulate_events_thread(self, loop: asyncio.AbstractEventLoop):
        """Generate simulated events for testing when Kafka is unavailable."""
        import random
        from datetime import datetime, timezone

        zones = [
            "bkc_commercial", "hospital_zone", "airport_zone",
            "port_zone", "school_zone", "residential_zone", "highway_zone",
        ]
        protocols = ["HTTP", "HTTPS", "MQTT", "CoAP"]
        event_types = ["network_event", "sensor_reading", "device_event", "cyber_alert"]
        methods = ["GET", "POST", "PUT", "DELETE"]
        endpoints = [
            "/api/lights/status", "/api/sensors/data", "/api/devices/heartbeat",
            "/api/config/update", "/api/firmware/check", "/api/metrics/push",
        ]

        while self.running:
            self.event_count += 1
            zone = random.choice(zones)
            etype = random.choice(event_types)

            event = {
                "id": self.event_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": etype,
                "zone_id": zone,
            }

            if etype == "network_event":
                event.update({
                    "source_ip": f"10.{random.randint(1,7)}.{random.randint(1,254)}.{random.randint(1,254)}",
                    "destination_ip": f"10.{random.randint(1,7)}.0.1",
                    "destination_port": random.choice([80, 443, 1883, 5683, 8080]),
                    "protocol": random.choice(protocols),
                    "method": random.choice(methods),
                    "endpoint": random.choice(endpoints),
                    "status_code": random.choices([200, 201, 204, 301, 400, 403, 404, 500], weights=[50, 10, 5, 3, 5, 3, 5, 2])[0],
                    "response_time_ms": round(random.uniform(1, 500), 1),
                    "bytes_sent": random.randint(64, 4096),
                    "bytes_received": random.randint(128, 8192),
                })
            elif etype == "sensor_reading":
                event.update({
                    "device_id": f"sensor_{zone[:3]}_{random.randint(1,50):03d}",
                    "device_type": random.choice(["ambient_light", "motion", "power_meter", "temperature"]),
                    "metrics": {
                        "ambient_lux": round(random.uniform(0, 1000), 1),
                        "power_watts": round(random.uniform(5, 150), 1),
                        "brightness_pct": random.randint(0, 100),
                        "motion_detected": random.random() < 0.2,
                        "temperature_c": round(random.uniform(18, 45), 1),
                    },
                })
            elif etype == "device_event":
                event.update({
                    "device_id": f"light_{zone[:3]}_{random.randint(1,100):03d}",
                    "device_type": "smart_light",
                    "event_subtype": random.choice(["heartbeat", "config_change", "firmware_update", "reboot", "error"]),
                    "status": random.choice(["online", "online", "online", "degraded", "offline"]),
                    "firmware_version": f"2.{random.randint(1,5)}.{random.randint(0,9)}",
                })
            elif etype == "cyber_alert":
                event.update({
                    "source_ip": f"10.{random.randint(1,7)}.{random.randint(1,254)}.{random.randint(1,254)}",
                    "destination_ip": f"10.{random.randint(1,7)}.0.1",
                    "protocol": random.choice(protocols),
                    "alert_type": random.choice(["port_scan", "brute_force", "anomalous_traffic", "unauthorized_access", "malware_signature"]),
                    "severity": random.choice(["low", "medium", "high", "critical"]),
                    "description": "Suspicious activity detected",
                })

            msg = json.dumps(event)
            self._event_buffer.append(msg)
            if len(self._event_buffer) > 5000:
                self._event_buffer = self._event_buffer[-3000:]

            asyncio.run_coroutine_threadsafe(self.broadcast(msg), loop)

            # Vary rate: 10-50 events/sec
            time.sleep(random.uniform(0.02, 0.1))

    async def _send_stats(self):
        """Periodically send stats to clients."""
        while self.running:
            stats = json.dumps({
                "type": "stats",
                "total_events": self.event_count,
                "connected_clients": len(self.clients),
                "buffer_size": len(self._event_buffer),
            })
            await self.broadcast(stats)
            await asyncio.sleep(5)

    def _start_http_server(self):
        """Serve log_viewer.html on HTTP."""
        html_dir = str(HTML_FILE.parent)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=html_dir, **kwargs)

            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self.path = "/log_viewer.html"
                return super().do_GET()

            def log_message(self, format, *args):
                pass  # Suppress HTTP logs

        httpd = HTTPServer(("0.0.0.0", self.http_port), Handler)
        logger.info(f"HTTP server: http://localhost:{self.http_port}")
        httpd.serve_forever()

    async def start(self):
        """Start the WebSocket server and Kafka consumer."""
        if not WS_AVAILABLE:
            logger.error("Cannot start: 'websockets' package is required")
            logger.error("Install with: pip install websockets")
            return

        self.running = True
        loop = asyncio.get_event_loop()

        # Start HTTP server in background thread
        http_thread = threading.Thread(target=self._start_http_server, daemon=True)
        http_thread.start()

        # Start Kafka consumer in background thread
        kafka_thread = threading.Thread(
            target=self._kafka_consumer_thread,
            args=(loop,),
            daemon=True,
        )
        kafka_thread.start()

        # Start stats broadcaster
        asyncio.ensure_future(self._send_stats())

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║         ARENA LOG VIEWER — SERVER                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🌐 Open in browser:  http://localhost:{self.http_port:<24}║
║  📡 WebSocket:        ws://localhost:{self.ws_port:<25}║
║  📊 Kafka:            {self.kafka_servers:<37}║
║  📺 Topics:           {', '.join(KAFKA_TOPICS):<37}║
║                                                              ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
""")

        # Start WebSocket server
        async with websockets.serve(self.ws_handler, "0.0.0.0", self.ws_port):
            logger.info(f"WebSocket server: ws://localhost:{self.ws_port}")
            await asyncio.Future()  # Run forever


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Arena Log Viewer Server")
    parser.add_argument("--port", type=int, default=8888, help="HTTP port (WS = port+1)")
    parser.add_argument("--kafka", default="localhost:19092", help="Kafka bootstrap servers")
    args = parser.parse_args()

    server = LogServer(
        kafka_servers=args.kafka,
        http_port=args.port,
        ws_port=args.port + 1,
    )

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        server.running = False
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
