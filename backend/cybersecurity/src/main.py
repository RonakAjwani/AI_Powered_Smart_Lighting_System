# backend/cybersecurity/src/main.py

"""
Cybersecurity Microservice — FastAPI entry point.

Exposes REST & WebSocket endpoints for:
  • DDoS & Malware agent analysis
  • Runtime configuration management (GET/PUT)
  • Network simulator control (start/stop/attack)
  • Real-time event streaming via WebSocket
  • Metrics & timeline data for dashboard charts
"""

import asyncio
import json
import logging
import uuid
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from .config.settings import config
from .agents.ddos_detection_agent import ddos_detection_agent, DDoSDetectionState
from .agents.malware_detection_agent import malware_detection_agent, MalwareDetectionState
from .graph.cybersecurity_graph import cybersecurity_graph
from .simulator.network_simulator import network_simulator, MUMBAI_ZONES

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# WebSocket Connection Manager
# ═════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.event_buffer: deque = deque(maxlen=200)
        self._metrics_buffer: deque = deque(maxlen=3000)  # ~5 min at 10 events/sec

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
        # Send buffered events so new clients catch up
        try:
            await websocket.send_json({
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "buffered_events": len(self.event_buffer),
            })
            for event in list(self.event_buffer):
                await websocket.send_json(event)
        except Exception:
            pass

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        self.event_buffer.append(message)
        self._metrics_buffer.append(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def get_timeline_metrics(self, window_seconds: int = 300, bucket_seconds: int = 10) -> List[Dict]:
        """Aggregate events into time buckets for the timeline chart."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        num_buckets = window_seconds // bucket_seconds

        buckets = []
        for i in range(num_buckets):
            bucket_start = cutoff + timedelta(seconds=i * bucket_seconds)
            bucket_end = bucket_start + timedelta(seconds=bucket_seconds)
            buckets.append({
                "time": bucket_start.isoformat(),
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "ddos": 0,
                "malware": 0,
                "normal": 0,
            })

        for event in self._metrics_buffer:
            data = event.get("data", event)
            try:
                ts = datetime.fromisoformat(data.get("timestamp", ""))
            except (ValueError, TypeError):
                continue
            if ts < cutoff:
                continue
            bucket_idx = min(int((ts - cutoff).total_seconds() / bucket_seconds), num_buckets - 1)
            if 0 <= bucket_idx < len(buckets):
                buckets[bucket_idx]["total"] += 1
                severity = data.get("severity", "low")
                if severity in buckets[bucket_idx]:
                    buckets[bucket_idx][severity] += 1
                # Categorize by event type
                evt_type = data.get("event_type", "")
                if "ddos" in evt_type or evt_type in ("network_traffic", "connection_attempt"):
                    if data.get("suspicious"):
                        buckets[bucket_idx]["ddos"] += 1
                    else:
                        buckets[bucket_idx]["normal"] += 1
                elif evt_type in ("process_execution", "file_system_change", "device_behavior", "firmware_check"):
                    if data.get("suspicious"):
                        buckets[bucket_idx]["malware"] += 1
                    else:
                        buckets[bucket_idx]["normal"] += 1
                else:
                    buckets[bucket_idx]["normal"] += 1

        return buckets

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Aggregate stats for dashboard summary cards and charts."""
        now = datetime.now()
        cutoff_5m = now - timedelta(minutes=5)

        total = 0
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}
        by_zone = {}
        suspicious_count = 0

        for event in self._metrics_buffer:
            data = event.get("data", event)
            try:
                ts = datetime.fromisoformat(data.get("timestamp", ""))
            except (ValueError, TypeError):
                continue
            if ts < cutoff_5m:
                continue
            total += 1
            sev = data.get("severity", "low")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            evt_type = data.get("event_type", "unknown")
            by_type[evt_type] = by_type.get(evt_type, 0) + 1
            zone = data.get("zone_id", "unknown")
            by_zone[zone] = by_zone.get(zone, 0) + 1
            if data.get("suspicious"):
                suspicious_count += 1

        return {
            "window_seconds": 300,
            "total_events": total,
            "events_per_second": round(total / 300, 2),
            "by_severity": by_severity,
            "by_event_type": by_type,
            "by_zone": by_zone,
            "suspicious_events": suspicious_count,
            "threat_level": (
                "critical" if by_severity.get("critical", 0) > 3
                else "high" if by_severity.get("high", 0) > 5
                else "medium" if by_severity.get("medium", 0) > 10
                else "low"
            ),
            "timestamp": now.isoformat(),
        }


manager = ConnectionManager()

# ═════════════════════════════════════════════════════════════════════════════
# Lifespan (startup / shutdown)
# ═════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Cybersecurity service starting — 2-agent system (DDoS + Malware)")
    # Start simulator automatically so events flow on boot
    network_simulator.start()
    # Background task to forward simulator events to WebSocket
    ws_task = asyncio.create_task(_forward_simulator_events())
    yield
    network_simulator.stop()
    ws_task.cancel()
    logger.info("Cybersecurity service shutdown complete")

async def _forward_simulator_events():
    """Continuously forward simulator's recent events to WebSocket clients."""
    last_index = 0
    while True:
        try:
            events = list(network_simulator.recent_events)
            new_events = events[last_index:]
            for event in new_events:
                ws_message = {
                    "type": "kafka_event",
                    "data": event,
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(ws_message)
            last_index = len(events)
            # Also broadcast periodic status
            if last_index % 20 == 0:
                status_msg = {
                    "type": "system_status",
                    "data": {
                        "agents": {
                            "ddos_detection": "active",
                            "malware_detection": "active",
                        },
                        "simulator": network_simulator.get_status(),
                        "timestamp": datetime.now().isoformat(),
                    },
                }
                await manager.broadcast(status_msg)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"WS forwarder error: {e}")
        await asyncio.sleep(0.5)


# ═════════════════════════════════════════════════════════════════════════════
# FastAPI App
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Cybersecurity Agent Service",
    description="2-Agent Cybersecurity System — DDoS & Malware Detection with Network Simulator",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

# ═════════════════════════════════════════════════════════════════════════════
# Request / Response Models
# ═════════════════════════════════════════════════════════════════════════════

class SecurityAnalysisRequest(BaseModel):
    analysis_type: str = "full"
    time_window: int = 300
    priority: str = "normal"

class EventIngestRequest(BaseModel):
    event_type: str
    data: Dict[str, Any] = {}
    severity: str = "medium"

class AttackTriggerRequest(BaseModel):
    type: str = "ddos_flood"
    zone: str = "SL-ZONE-A"
    intensity: float = 0.8
    duration: int = 30

class ZoneCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    area: str = "Custom Area"
    type: str = "custom"
    center: List[float] = [19.076, 72.877]
    bounds: List[List[float]] = [[19.073, 72.874], [19.079, 72.880]]
    device_count: int = 5
    priority: str = "medium"
    color: str = "#6b7280"


# ═════════════════════════════════════════════════════════════════════════════
# Health & Status Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cybersecurity",
        "agents": ["ddos_detection", "malware_detection"],
        "simulator": network_simulator.is_running,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/status/agents")
async def get_agents_status():
    return {
        "agents": {
            "ddos_detection": {
                "status": "active",
                "capabilities": [
                    "HTTP Flood Detection", "SYN Flood Detection",
                    "UDP Flood Detection", "Volumetric Attack Detection",
                    "Geographic Anomaly Detection", "Rate Limiting",
                ],
            },
            "malware_detection": {
                "status": "active",
                "capabilities": [
                    "Ransomware Detection", "Trojan Detection",
                    "Botnet Detection", "C2 Communication Detection",
                    "Firmware Integrity Check", "Behavioral Analysis",
                ],
            },
        },
        "graph_status": "operational",
        "system_mode": "2-agent parallel detection",
        "timestamp": datetime.now().isoformat(),
    }


# ═════════════════════════════════════════════════════════════════════════════
# Configuration Endpoints (GET / PUT / Reset)
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/config/ddos")
async def get_ddos_config():
    return config.get_ddos_config()

@app.get("/config/malware")
async def get_malware_config():
    return config.get_malware_config()

@app.get("/config/all")
async def get_all_config():
    return {
        "ddos": config.get_ddos_config(),
        "malware": config.get_malware_config(),
        "timestamp": datetime.now().isoformat(),
    }

@app.put("/config/ddos")
async def update_ddos_config(data: Dict[str, Any]):
    result = config.update_ddos_config(data)
    return {"status": "updated", **result}

@app.put("/config/malware")
async def update_malware_config(data: Dict[str, Any]):
    result = config.update_malware_config(data)
    return {"status": "updated", **result}

@app.post("/config/reset")
async def reset_config():
    config.reset_to_defaults()
    return {
        "status": "reset",
        "message": "All configuration reset to defaults",
        "config": {
            "ddos": config.get_ddos_config(),
            "malware": config.get_malware_config(),
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# Analysis Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/analyze/security")
async def analyze_security(request: SecurityAnalysisRequest, background_tasks: BackgroundTasks):
    analysis_id = str(uuid.uuid4())
    try:
        if request.analysis_type == "ddos":
            result = cybersecurity_graph.execute_ddos_analysis()
        elif request.analysis_type == "malware":
            result = cybersecurity_graph.execute_malware_analysis()
        else:
            result = cybersecurity_graph.execute_cybersecurity_analysis()

        # Broadcast result to WebSocket clients
        ws_msg = {
            "type": "analysis_result",
            "data": {
                "analysis_id": analysis_id,
                "analysis_type": request.analysis_type,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            },
        }
        background_tasks.add_task(asyncio.ensure_future, manager.broadcast(ws_msg))

        return {
            "analysis_id": analysis_id,
            "analysis_type": request.analysis_type,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {
            "analysis_id": analysis_id,
            "error": str(e),
            "status": "failed",
        }

@app.post("/analyze/ddos")
async def analyze_ddos():
    result = cybersecurity_graph.execute_ddos_analysis()
    return {"detection_id": str(uuid.uuid4()), "result": result}

@app.post("/analyze/malware")
async def analyze_malware():
    result = cybersecurity_graph.execute_malware_analysis()
    return {"detection_id": str(uuid.uuid4()), "result": result}


# ═════════════════════════════════════════════════════════════════════════════
# Event Ingestion Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/events/ddos")
async def ingest_ddos_event(request: EventIngestRequest):
    event_id = str(uuid.uuid4())
    logger.info(f"DDoS event ingested: {event_id}")
    return {"event_id": event_id, "published": True}

@app.post("/events/malware")
async def ingest_malware_event(request: EventIngestRequest):
    event_id = str(uuid.uuid4())
    logger.info(f"Malware event ingested: {event_id}")
    return {"event_id": event_id, "published": True}

@app.post("/events/batch")
async def ingest_batch_events(events: List[EventIngestRequest]):
    results = []
    for event in events:
        event_id = str(uuid.uuid4())
        results.append({"event_id": event_id, "type": event.event_type, "published": True})
    return {"processed": len(results), "results": results}


# ═════════════════════════════════════════════════════════════════════════════
# Simulator Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/simulator/start")
async def start_simulator():
    result = network_simulator.start()
    return result

@app.post("/simulator/stop")
async def stop_simulator():
    result = network_simulator.stop()
    return result

@app.get("/simulator/status")
async def simulator_status():
    return network_simulator.get_status()

@app.get("/simulator/zones")
async def simulator_zones():
    return network_simulator.get_zones()

@app.post("/simulator/attack")
async def trigger_attack(request: AttackTriggerRequest):
    result = network_simulator.trigger_attack(
        attack_type=request.type,
        zone_id=request.zone,
        intensity=request.intensity,
        duration=request.duration,
    )
    return result

@app.post("/simulator/zones")
async def add_zone(request: ZoneCreateRequest):
    zone_data = request.model_dump()
    result = network_simulator.add_zone(zone_data)
    return result


# ═════════════════════════════════════════════════════════════════════════════
# Metrics Endpoints (for Dashboard Charts)
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/metrics/timeline")
async def metrics_timeline(window: int = 300, bucket: int = 10):
    return manager.get_timeline_metrics(window_seconds=window, bucket_seconds=bucket)

@app.get("/metrics/summary")
async def metrics_summary():
    return manager.get_metrics_summary()


# ═════════════════════════════════════════════════════════════════════════════
# WebSocket Endpoint
# ═════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — client can also send commands
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
