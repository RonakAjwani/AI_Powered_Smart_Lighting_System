# Cybersecurity Admin Dashboard — Final Research & Brainstorm

## 1. Mumbai Infrastructure Zones

Real Mumbai locations with actual coordinates for the smart lighting simulation:

| Zone ID | Name | Category | Lat | Lng | Devices | Significance |
|---------|------|----------|-----|-----|---------|-------------|
| `zone-nariman` | Nariman Point | 🏦 Financial | 18.925 | 72.825 | 20 | Financial district, high-value target |
| `zone-bkc` | BKC Business Hub | 🏢 Corporate | 19.065 | 72.870 | 25 | Corporate HQs, banks, stock exchange |
| `zone-airport` | CSIA Airport | ✈️ Critical Infra | 19.097 | 72.874 | 30 | International airport, critical infrastructure |
| `zone-andheri` | Andheri MIDC | 🏭 Industrial | 19.118 | 72.863 | 20 | Industrial manufacturing, MIDC zone |
| `zone-powai` | Powai Tech Park | 💻 Technology | 19.116 | 72.905 | 15 | IIT Bombay, tech companies, data centers |
| `zone-bandra` | Bandra Residential | 🏠 Residential | 19.060 | 72.835 | 15 | Dense residential, public lighting |
| `zone-jnpt` | JNPT Port | 🚢 Port | 18.970 | 72.930 | 10 | Major cargo port, maritime security |

**Device naming**: `SL-{ZONE_SHORT}-{NNN}` → `SL-BKC-014`, `SL-AIRPORT-003`, `SL-POWAI-008`

### Dynamic Zone Management (from Admin Dashboard)

Admin should be able to:
- **Add new zone**: Name, category, lat/lng bounds, device count
- **Edit zone**: Modify boundaries, rename, change category
- **Delete zone**: Remove zone and associated devices
- **View zone health**: Color-coded map polygons (🟢 safe / 🟡 warning / 🔴 attack)

**Persistence**: Zones saved to `zones_config.json` on backend, loaded at startup.

---

## 2. Configurable Agentic Pipeline Parameters

### Complete Parameter Catalogue

After analysing every file in the pipeline ([settings.py](file:///c:/Projects/AI_Powered_Smart_Lighting_System/backend/power/src/config/settings.py), [ddos_detection_agent.py](file:///c:/Projects/AI_Powered_Smart_Lighting_System/backend/cybersecurity/src/agents/ddos_detection_agent.py), [malware_detection_agent.py](file:///c:/Projects/AI_Powered_Smart_Lighting_System/backend/cybersecurity/src/agents/malware_detection_agent.py), [cybersecurity_graph.py](file:///c:/Projects/AI_Powered_Smart_Lighting_System/backend/cybersecurity/src/graph/cybersecurity_graph.py)), here are **all** configurable parameters:

#### Category 1: DDoS Detection Thresholds (13 params)

| Parameter | Current Default | Config Key | What It Controls |
|-----------|----------------|------------|-----------------|
| Normal RPS Min | 100 | `DDOS_NORMAL_RPS_MIN` | Lower bound of expected traffic |
| Normal RPS Max | 500 | `DDOS_NORMAL_RPS_MAX` | Upper bound — above = suspicious |
| High RPS | 2500 | `DDOS_HIGH_RPS` | High severity trigger |
| Critical RPS | 5000 | `DDOS_CRITICAL_RPS` | Critical severity trigger (10x normal) |
| Requests/IP Threshold | 1000 | `DDOS_REQUESTS_PER_IP_THRESHOLD` | Max requests from single IP/min |
| Unique IP Normal | 200 | `DDOS_UNIQUE_IP_NORMAL_MAX` | Expected unique IPs |
| Unique IP Attack | 500 | `DDOS_UNIQUE_IP_ATTACK_MIN` | Botnet indicator threshold |
| Response Time Normal | 100ms | `DDOS_RESPONSE_TIME_NORMAL_MS` | Expected response time |
| Failed Request Rate | 2% | `DDOS_FAILED_REQUEST_RATE_NORMAL` | Expected failure rate |
| SYN Flood Threshold | 10000 | `DDOS_SYN_FLOOD_THRESHOLD` | SYN flood detection |
| Packet Size Min | 10 bytes | `DDOS_PACKET_SIZE_ANOMALY_MIN` | Suspiciously small packets |
| Packet Size Max | 65000 bytes | `DDOS_PACKET_SIZE_ANOMALY_MAX` | Suspiciously large packets |
| Geo Concentration | 80% | `DDOS_GEO_CONCENTRATION_THRESHOLD` | Single-region traffic concentration |

#### Category 2: Malware Detection Thresholds (8 numeric params)

| Parameter | Current Default | Config Key | What It Controls |
|-----------|----------------|------------|-----------------|
| File Encryption Rate | 100 files/min | `MALWARE_FILE_ENCRYPTION_RATE_THRESHOLD` | Ransomware detection |
| Outbound Connections Normal | 10 | `MALWARE_OUTBOUND_CONNECTIONS_NORMAL` | Expected outbound connections |
| Outbound Connections Suspicious | 50 | `MALWARE_OUTBOUND_CONNECTIONS_SUSPICIOUS` | C2 indicator |
| File Modifications Normal | 20 | `MALWARE_FILE_MODIFICATIONS_NORMAL` | Expected file changes |
| File Modifications Suspicious | 100 | `MALWARE_FILE_MODIFICATIONS_SUSPICIOUS` | Ransomware indicator |
| CPU Usage Normal | 70% | `MALWARE_CPU_USAGE_NORMAL` | Expected CPU |
| CPU Usage Suspicious | 95% | `MALWARE_CPU_USAGE_SUSPICIOUS` | Cryptominer/malware indicator |
| Network Upload Normal | 10 MB | `MALWARE_NETWORK_UPLOAD_NORMAL_MB` | Expected upload volume |

#### Category 3: Malware Signatures (advanced — 8 list params)

| Parameter | Current Value | GUI Element |
|-----------|--------------|-------------|
| Suspicious Extensions | `.enc`, `.locked`, `.crypto`, etc. | Editable tag list |
| Ransom Note Patterns | `README`, `HOW_TO_DECRYPT`, etc. | Editable tag list |
| C2 Ports | 4444, 5555, 6666, 8080, etc. | Editable number list |
| Suspicious Processes | `powershell.exe -enc`, etc. | Editable tag list |
| Known Malware Families | `mirai`, `wannacry`, `ryuk`, etc. | Editable tag list |
| Backup Deletion Keywords | `vssadmin`, `delete`, `shadows` | Editable tag list |
| Privilege Escalation Keywords | `mimikatz`, `procdump`, `lsass` | Editable tag list |
| Upload Suspicious MB | 100 MB | Slider/input |

#### Category 4: LLM Configuration (4 params × 3 instances)

| Parameter | Default | Instances | What It Controls |
|-----------|---------|-----------|-----------------|
| Model Name | `llama3-8b-8192` | DDoS Agent, Malware Agent, Graph Aggregator | Which LLM to use |
| Temperature | 0 / 0.1 | All three | Creativity vs precision |
| Max Tokens | 1024 | All three | Response length limit |
| API Key | from [.env](file:///c:/Projects/AI_Powered_Smart_Lighting_System/.env) | Shared | Authentication |

#### Category 5: Kafka & Infrastructure (7 params)

| Parameter | Default | What It Controls |
|-----------|---------|-----------------|
| Bootstrap Servers | `localhost:9092` | Kafka cluster address |
| Consumer Group | `cybersecurity_agents` | Consumer group ID |
| Network Events Topic | `network_events` | DDoS event topic |
| Device Events Topic | `device_events` | Malware event topic |
| Cyber Alerts Topic | `cyber_alerts` | Alert output topic |
| DDoS Alerts Topic | `ddos_alerts` | DDoS-specific alerts |
| Malware Alerts Topic | `malware_alerts` | Malware-specific alerts |

#### Category 6: Agent Execution (3 params)

| Parameter | Default | What It Controls |
|-----------|---------|-----------------|
| DDoS Agent Timeout | 30s | Max execution time |
| Malware Agent Timeout | 60s | Max execution time |
| Max Retries | 3 | Retry count on failure |

### What Should Be Exposed on Admin Dashboard?

**Recommended for dashboard configuration** (grouped by tabs):

| Tab | Parameters | Why |
|-----|-----------|-----|
| **DDoS Thresholds** | All 13 DDoS params | Core tuning for false positive/negative rates |
| **Malware Thresholds** | 8 numeric malware params | Detection sensitivity tuning |
| **Malware Signatures** | 8 list params | Add/remove detection patterns |
| **LLM Settings** | Model, temperature, max tokens | Model behavior tuning |
| **Agent Execution** | Timeouts, retries | Performance tuning |

**NOT recommended for dashboard** (leave as env vars):
- Kafka infrastructure settings (changing these at runtime = dangerous)
- API keys (security risk)

---

## 3. SOC Dashboard — Charts & Data Generation

### Chart-to-Data Mapping (ensuring no blank charts)

| Chart | Data Source | Simulator Must Generate |
|-------|-----------|----------------------|
| **Threat Timeline** (line) | Event timestamps + severity | ✅ Every event has `timestamp` + severity |
| **Mumbai Zone Map** (Leaflet) | Zone ID + security state | ✅ Events include `zone_id`, zone states computed |
| **Severity Distribution** (doughnut) | Severity counts | ✅ Events have [severity](file:///c:/Projects/AI_Powered_Smart_Lighting_System/backend/cybersecurity/src/agents/ddos_detection_agent.py#354-407) field |
| **Attack Type Breakdown** (bar) | Event type counts | ✅ Events have `event_type` |
| **Live IOC Feed** (table) | Attacker IPs, ports, hashes | ✅ Network events have `source_ip`, `destination_port` |
| **Agent Activity Log** (feed) | Agent messages/actions | ✅ WebSocket broadcasts agent results |
| **MTTD Gauge** | Detection timestamps | ✅ Track time between event creation → agent detection |
| **MTTR Gauge** | Mitigation timestamps | ✅ Track time between detection → mitigation action |
| **Events/sec Sparkline** | Event count per second | ✅ Count events in rolling window |
| **Active Incidents** (badge) | Unresolved attack count | ✅ Track active attacks |
| **Top Attacking IPs** (bar) | Source IP frequency | ✅ Events have `source_ip` |
| **Network Traffic Volume** (area) | Event count over time | ✅ Event timestamps |
| **Device Health Grid** (heatmap) | Per-device status | ✅ Events have `device_id` + metrics |

> [!IMPORTANT]
> **Every chart has a guaranteed data source.** The simulator will generate events with all required fields. During normal baseline, charts show calm/green data. During attack triggers, charts spike with red/critical data.

---

## 4. Summary of Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Simulator type | Custom backend + optional soc-faker | Exact schema match, Kafka-native, controllable |
| Mumbai zones | 7 real infrastructure zones | Realistic, demo-impressive |
| Zone management | Dynamic CRUD from dashboard | Mentor feedback: admin = customization |
| Attack triggers | Manual buttons, 6 scenarios | Demo-friendly, no waiting |
| Charts | 13 chart types, SOC-grade | Human supervisor can detect what agents miss |
| Config params | 5 groups, 50+ params | Complete pipeline control |
| Config persistence | JSON file per category | Survives restarts |
| What NOT to expose | Kafka infra, API keys | Security + stability |
