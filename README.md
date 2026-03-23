# AI-Powered Smart Lighting System - Cybersecurity Focus

## Introduction
This project secures smart-lighting infrastructure using an AI-driven cybersecurity microservice. The system detects DDoS and malware threats from live telemetry, scores severity, and produces response actions that can be consumed by dashboards or downstream controllers.

The cybersecurity service is implemented with FastAPI, LangGraph, LangChain, Kafka, and Groq LLMs. It also includes a built-in network/device event simulator to support demonstration and evaluation workflows.

## Problem Statement
Smart-lighting deployments operate as distributed cyber-physical systems with many edge devices, zones, and network paths. These environments face two major threat classes:

1. DDoS-style network abuse that degrades availability.
2. Malware behavior on edge devices that affects integrity and control.

Traditional static monitoring is often too slow for correlated, real-time incident triage. The project needs an approach that can ingest streaming telemetry, identify attack patterns quickly, and surface actionable response guidance.

## Our Solution
The cybersecurity component provides a dual-agent detection pipeline:

1. A DDoS detection agent that analyzes traffic-rate, protocol, IP-distribution, and connection-level anomalies.
2. A malware detection agent that analyzes file-system, process, network, and firmware-integrity behavior.
3. A LangGraph orchestrator that runs both agents in parallel and uses LLM-assisted aggregation to produce a combined risk posture and top priority actions.

Operational outputs include:

1. REST endpoints for full and per-domain analysis.
2. Real-time event streaming support for dashboard clients.
3. Metrics and timeline summaries for SOC-style monitoring.
4. Configurable thresholds/signatures for runtime tuning.

## Methodology
The methodology follows a streaming, agentic detection workflow:

1. Telemetry Ingestion
    Events are consumed from Kafka topics and simulator streams (network + device behavior) inside rolling time windows.

2. Domain-Specific Feature Extraction
    DDoS features: requests/sec, unique IPs, per-IP concentration, response latency, failed request rate, SYN-heavy patterns, packet-size anomalies.
    Malware features: encryption behavior, suspicious extensions/processes, C2-like ports, outbound transfer volume, firmware integrity signals.

3. Agent-Level Reasoning
    Each agent runs a LangGraph pipeline to collect data, compute metrics, detect threat signals, assess severity, and propose mitigation/remediation steps.

4. Cross-Agent Aggregation
    A parent cybersecurity graph executes both agents in parallel and uses LLM-based aggregation to determine overall risk level and top 3 priority actions.

5. Exposure and Monitoring
    Findings are exposed through FastAPI endpoints, WebSocket feeds, and Prometheus metrics for operational dashboards.

## System Architecture
<img width="1024" height="575" alt="image" src="https://github.com/user-attachments/assets/988c9203-b88b-40e0-b07e-09fd5b39ab53" />

## Agents and their roles in tabular format
| Agent | Primary Role | Input Signals | Main Outputs |
|---|---|---|---|
| DDoS Detection Agent | Detect network-layer and application-layer flooding attacks | `network_events`, `cyber_alerts`, traffic telemetry (IP, protocol, packet size, status, latency) | `attack_detected`, `attack_type`, severity, attacker IPs, mitigation actions |
| Malware Detection Agent | Detect malware/ransomware behavior on smart-lighting devices | `sensor_data`, `device_events`, `cyber_alerts`, process/file/network/firmware events | `malware_detected`, family/type, indicators of compromise, affected devices, remediation steps |
| Cybersecurity Graph Aggregator | Correlate DDoS + malware outputs into one operational posture | Agent results, confidence/severity summaries | Overall risk level, combined summary, top priority actions |

## Dataset details
The cybersecurity benchmark dataset is in [datasets/](datasets) and is organized as:

1. [datasets/ddos/](datasets/ddos): normal traffic + 6 attack families.
2. [datasets/malware/](datasets/malware): normal behavior + 5 malware families.

Current snapshot summary:

1. Total rows: 1012
2. Attack rows: 783
3. Normal rows: 229
4. Binary split: ~77.4% attack / ~22.6% normal

DDoS files include:

1. `normal_traffic.csv`
2. `http_flood_sample.csv`
3. `syn_flood_sample.csv`
4. `upd_flood.csv` (label taxonomy uses `udp_flood`)
5. `slowloris.csv`
6. `dns_amplification.csv`
7. `volumetric.csv`

Malware files include:

1. `normal_behavior_sample.csv`
2. `ransomware_sample.csv`
3. `trojan_sample.csv`
4. `botnet.csv`
5. `spyware.csv`
6. `rootkit.csv`

Ground-truth labels are available in all files through `is_attack`, `attack_type`, and `severity`.

## Project setup guide
### Prerequisites
1. Docker Desktop (or Docker Engine + Compose)
2. Groq API key
3. Git

### 1) Clone and enter project
```bash
git clone <your-repo-url>
cd AI_Powered_Smart_Lighting_System
```

### 2) Create environment file
Create a root `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
WEATHERAPI_API_KEY=optional_for_weather_service
```

For cybersecurity-only usage, `GROQ_API_KEY` is the required key.

### 3) Build and start containers
```bash
docker-compose build
docker-compose up -d
```

### 4) Verify cybersecurity service
```bash
curl http://localhost:8000/health
curl http://localhost:8000/status/agents
```

### 5) Open useful interfaces
1. Cybersecurity API docs: http://localhost:8000/docs
2. Prometheus: http://localhost:9090
3. Grafana: http://localhost:3000
4. Kafka UI: http://localhost:8080

### 6) Run analysis endpoints
Full analysis:
```bash
curl -X POST "http://localhost:8000/analyze/security" \
  -H "Content-Type: application/json" \
  -d '{"analysis_type":"full","time_window":300,"priority":"high"}'
```

DDoS only:
```bash
curl -X POST "http://localhost:8000/analyze/ddos"
```

Malware only:
```bash
curl -X POST "http://localhost:8000/analyze/malware"
```

### 7) Stop services
```bash
docker-compose down
```

For implementation-level details of the cybersecurity microservice, see [backend/cybersecurity/README.md](backend/cybersecurity/README.md).
