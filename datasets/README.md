# AI-Powered Smart Lighting Cybersecurity Datasets

This dataset package is intentionally minimal and contains only:
- `ddos/` (DDoS benchmark CSV files)
- `malware/` (malware benchmark CSV files)
- this `README.md`

It is designed for reproducible evaluation of two agents in your project:
1. DDoS detection agent
2. Malware detection agent

The data combines benign and malicious behavior with explicit ground-truth labels (`is_attack`, `attack_type`, `severity`) to support binary and multi-class benchmarking.

---

## 1) Folder Structure

```text
datasets/
├── README.md
├── ddos/
│   ├── normal_traffic.csv
│   ├── http_flood_sample.csv
│   ├── syn_flood_sample.csv
│   ├── upd_flood.csv
│   ├── slowloris.csv
│   ├── dns_amplification.csv
│   └── volumetric.csv
└── malware/
    ├── normal_behavior_sample.csv
    ├── ransomware_sample.csv
    ├── trojan_sample.csv
    ├── botnet.csv
    ├── spyware.csv
    └── rootkit.csv
```

---

## 2) Dataset Goals and Scope

### Primary goals
- Stress-test detection logic across major DDoS and malware families.
- Benchmark false positives on realistic normal telemetry.
- Evaluate severity-aware decision quality (not only attack/no-attack).
- Support conference-style reporting with traceable references.

### Scope covered
- **DDoS families**: HTTP Flood, SYN Flood, UDP Flood, Slowloris, DNS Amplification, Volumetric.
- **Malware families**: Ransomware, Trojan, Botnet, Spyware, Rootkit.
- **Operational context**: Multi-zone smart-lighting infrastructure with diverse device IDs and telemetry event types.

### Out of scope (current version)
- Payload/deep packet content.
- Real malware binaries.
- Full PCAP or long-duration packet flow reconstructions.

---
## 3) File-by-File Detail

### DDoS datasets (`ddos/`)

| File | Rows | Attack Rows | Normal Rows | Main attack label(s) | Key use case |
|---|---:|---:|---:|---|---|
| `normal_traffic.csv` | 95 | 0 | 95 | `none` | Baseline/FPR validation |
| `http_flood_sample.csv` | 56 | 51 | 5 | `http_flood` | Layer-7 request flood detection |
| `syn_flood_sample.csv` | 30 | 29 | 1 | `syn_flood` | Half-open TCP flood detection |
| `upd_flood.csv` | 120 | 100 | 20 | `udp_flood` | L3/L4 UDP flood behavior |
| `slowloris.csv` | 120 | 100 | 20 | `slowloris` | Low-and-slow connection exhaustion |
| `dns_amplification.csv` | 120 | 110 | 10 | `dns_amplification` | Reflection/amplification detection |
| `volumetric.csv` | 120 | 105 | 15 | `volumetric` | Multi-vector high-bandwidth flood |

### Malware datasets (`malware/`)

| File | Rows | Attack Rows | Normal Rows | Main attack label(s) | Key use case |
|---|---:|---:|---:|---|---|
| `normal_behavior_sample.csv` | 21 | 0 | 21 | `none` | Benign baseline/FPR testing |
| `ransomware_sample.csv` | 30 | 29 | 1 | `ransomware` | Encryption-burst behavior |
| `trojan_sample.csv` | 30 | 29 | 1 | `trojan` | Backdoor + C2 pattern detection |
| `botnet.csv` | 90 | 75 | 15 | `botnet` | Beaconing/recruitment pattern detection |
| `spyware.csv` | 90 | 75 | 15 | `spyware` | Stealth access + exfil-like behavior |
| `rootkit.csv` | 90 | 80 | 10 | `rootkit` | Persistence + integrity tampering |

### Package-level totals (current snapshot)
- **Total rows**: 1012
- **Attack rows**: 783
- **Normal rows**: 229
- **Binary class split**: ~77.4% attack / ~22.6% normal

Note: counts are for the current committed CSV snapshot and may change if files are regenerated.

---

## 4) What Each Attack Signature Represents

### DDoS signature logic
- **HTTP Flood**: very high request burst behavior + elevated application error responses (e.g., 429/503) + latency degradation.
- **SYN Flood**: sustained SYN-heavy connection attempts with handshake completion asymmetry.
- **UDP Flood** (`upd_flood.csv`): abnormally high UDP packet rate and burst intensity, often with large packets.
- **Slowloris**: many long-lived, partially completed requests and slow header/data trickle behavior.
- **DNS Amplification**: UDP/53-centric reflection profile with oversized response-like traffic.
- **Volumetric**: multi-protocol saturation pattern causing broad service performance degradation.

### Malware signature logic
- **Ransomware**: rapid encryption/modification, suspicious extension behavior, high CPU/memory pressure.
- **Trojan**: hidden or suspicious process execution with outbound C2-style network activity.
- **Botnet**: beaconing cadence, suspicious ports, process artifacts linked to command infrastructure.
- **Spyware**: stealth process behavior, sensitive file interactions, and outbound exfil-like transfer signals.
- **Rootkit**: deep persistence indicators, firmware/module tampering, and failed integrity checks.

---

## 5) Dataset Schemas and Semantics

### DDoS CSV schema (16 columns)

| Column | Meaning | Typical values |
|---|---|---|
| `timestamp` | Event time (UTC ISO-8601) | `2026-03-04T16:00:00.000Z` |
| `event_type` | Event category | `http_request`, `network_traffic`, `connection_attempt` |
| `source_ip` | Traffic source IP | IPv4 |
| `destination_ip` | Target IP | IPv4 |
| `destination_port` | Target service port | `80`, `443`, `53`, `22` |
| `protocol` | Network/application protocol | `HTTP`, `HTTPS`, `TCP`, `UDP`, `ICMP` |
| `packet_size` | Packet size in bytes | numeric |
| `connection_type` | Transport/session marker | `ACK`, `SYN`, `UDP`, `KEEP_ALIVE` |
| `response_time_ms` | Response latency | numeric ms |
| `status_code` | Response indicator | HTTP code or `0` |
| `geo_location` | Source geo tag | country/region string |
| `zone_id` | Smart-city zone identifier | `zone-bkc`, etc. |
| `device_id` | Device identifier | `SL-...` |
| `is_attack` | Binary ground truth | `true`, `false` |
| `attack_type` | Multi-class label | `none`, `http_flood`, `syn_flood`, `udp_flood`, `slowloris`, `dns_amplification`, `volumetric` |
| `severity` | Impact class | `none`, `low`, `medium`, `high`, `critical` |

### Malware CSV schema (19 columns)

| Column | Meaning | Typical values |
|---|---|---|
| `timestamp` | Event time (UTC ISO-8601) | `2026-03-04T20:00:00.000Z` |
| `event_type` | Device telemetry event class | `device_behavior`, `file_system_change`, `network_connection`, `process_execution`, `firmware_check` |
| `device_id` | Device identifier | `SL-...` |
| `zone_id` | Zone identifier | `zone-...` |
| `cpu_usage` | CPU utilization (%) | numeric |
| `memory_usage_mb` | Memory usage (MB) | numeric |
| `action` | Action observed | `modify`, `encrypt`, `create`, `hide`, `tamper` |
| `file_path` | File path involved | path string |
| `file_name` | File name involved | string |
| `direction` | Traffic direction | `outbound`, `inbound`, blank |
| `destination_ip` | Remote endpoint | IPv4 or blank |
| `destination_port` | Remote endpoint port | numeric or blank |
| `upload_bytes` | Outbound volume | numeric or blank |
| `command_line` | Executed command | string or blank |
| `process_name` | Process identifier | string or blank |
| `integrity_check` | Integrity outcome | `passed`, `warning`, `failed` |
| `is_attack` | Binary ground truth | `true`, `false` |
| `attack_type` | Multi-class label | `none`, `ransomware`, `trojan`, `botnet`, `spyware`, `rootkit` |
| `severity` | Impact class | `none`, `low`, `medium`, `high`, `critical` |

---

## 6) Labeling Policy

- **Benign rows**: `is_attack=false`, `attack_type=none`, `severity=none`.
- **Malicious rows**: `is_attack=true` with explicit family and severity.
- **Onset realism**: several attack files include a small benign prefix before attack escalation.
- **Evaluation recommendation**:
  - Binary task: predict `is_attack`
  - Multi-class task: predict `attack_type` when `is_attack=true`
  - Impact task: predict `severity`

---

## 7) Benchmarking Scenarios You Can Report in a Paper

1. **False-positive stress test**
   - Input only normal files, report FPR and precision.

2. **Family-wise single attack test**
   - Run each attack file independently to compute per-family recall/F1.

3. **Mixed-stream robustness test**
   - Concatenate benign + multiple attack files by timestamp to evaluate drift and onset detection.

4. **Severity calibration test**
   - Compare predicted severity vs labeled severity (macro-F1 / weighted-F1).

5. **Response quality test (agent behavior)**
   - Check if mitigation recommendations match attack family context.

Suggested metrics: Accuracy, Precision, Recall, F1, FPR, ROC-AUC (binary), MCC, and Time-To-Detect (TTD).

---

## 8) Data Quality and Reproducibility Notes

- Stable schema per folder (validated headers across all files).
- Ground-truth labels present in every dataset.
- Event ordering supports streaming simulation using `timestamp`.
- Multi-zone and multi-device identifiers improve operational realism.
- Recommended train/validation/test split strategy:
  - **By time** (preferred for streaming realism), or
  - **By file family** (for strict out-of-family generalization tests).

---

## 9) Reference-to-Dataset Traceability (What We Took From Each Source)

This section explicitly documents what was extracted from each cited source and how it influenced the dataset design.

| Ref | Source | Key things taken | How it appears in this dataset |
|---|---|---|---|
| 1 | MITRE ATT&CK for ICS | OT/ICS adversary behavior taxonomy; technique-oriented modeling of impact, persistence, and command/control patterns | Attack family definitions and behavior-style signatures across DDoS + malware classes |
| 2 | NIST SP 800-61 Rev.2 | Incident handling lifecycle; analysis and prioritization principles; severity-driven triage mindset | Inclusion of explicit `severity` labels and response-oriented use cases |
| 3 | NIST SP 800-94 | IDS/IPS-centric detection signals, anomaly/signature perspectives, network telemetry emphasis | Selection of network-centric DDoS features (rate/latency/status/protocol/ports) |
| 4 | NIST SP 800-82 Rev.2 | ICS-specific constraints (availability-first operations, segmented architecture, field device context) | Multi-zone device modeling and OT-aware attack scenarios |
| 5 | CIS Controls v8 | Practical defensive controls: monitoring, hardening, malware defenses, network control | Feature choices that map to SOC controls (integrity checks, suspicious outbound behavior, process anomalies) |
| 6 | OWASP IoT Top 10 | Common IoT weakness classes (insecure services, weak update/security posture, poor monitoring) | IoT-realistic malware scenarios, especially persistence, stealth process behavior, and endpoint compromise pathways |
| 7 | CISA ICS Advisories | Real-world OT threat case patterns and advisory-style detection cues | Attack realism and scenario framing for infrastructure-targeted threats |
| 8 | ENISA threat guidance | Threat landscape structuring and risk-led scenario composition for critical infrastructure | Prioritization of high-impact use cases and operationally relevant attack narratives |
| 9 | Cloudflare DDoS reports | Contemporary DDoS trends: HTTP floods, UDP floods, amplification, multi-vector spikes | Directly reflected in DDoS file families and volumetric/multi-vector patterns |
| 10 | Microsoft Digital Defense Report | Modern malware ecosystem patterns: ransomware operations, C2, credential/data theft trends | Malware family composition (`ransomware`, `trojan`, `botnet`, `spyware`) and outbound/C2 behavior features |
| 11 | Kaspersky IoT threat reports | IoT malware activity patterns and botnet behavior in connected devices | Botnet and spyware scenario realism, especially IoT endpoint-oriented telemetry |
| 12 | UNSW-NB15 methodology | Benchmark dataset construction principles for labeled cyber traffic and attack taxonomy balance | Structured normal+attack separation and benchmark-friendly labeling design |
| 13 | CICIDS2017 methodology | Realistic traffic profile philosophy; evaluation-friendly attack scenario structuring | File-level attack scenarios with benign context and practical benchmark usability |

---

## 10) Complete Reference List

1. MITRE ATT&CK for ICS. https://attack.mitre.org/matrices/ics/
2. NIST SP 800-61 Rev.2, *Computer Security Incident Handling Guide*. https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf
3. NIST SP 800-94, *Guide to Intrusion Detection and Prevention Systems*. https://csrc.nist.gov/publications/detail/sp/800-94/final
4. NIST SP 800-82 Rev.2, *Guide to Industrial Control Systems (ICS) Security*. https://csrc.nist.gov/publications/detail/sp/800-82/rev-2/final
5. CIS Critical Security Controls v8. https://www.cisecurity.org/controls/v8
6. OWASP IoT Top 10. https://owasp.org/www-project-internet-of-things/
7. CISA ICS Advisories. https://www.cisa.gov/news-events/ics-advisories
8. ENISA official portal and threat publications. https://www.enisa.europa.eu
9. Cloudflare DDoS Threat Intelligence and reports. https://www.cloudflare.com/ddos/
10. Microsoft Digital Defense Report. https://www.microsoft.com/security/security-insider/microsoft-digital-defense-report
11. Kaspersky threat intelligence / Securelist IoT reports. https://securelist.com
12. Moustafa, N. & Slay, J. (2015), UNSW-NB15 dataset/methodology reference.
13. Sharafaldin, I. et al. (2018), CICIDS2017 methodology reference.

---

## 11) Practical Usage Notes

- For binary detection training: target = `is_attack`.
- For multi-class attack-family testing: target = `attack_type` (filter `is_attack=true` rows if needed).
- For severity modeling: target = `severity`.
- For stream replay:
  1. sort by `timestamp`
  2. replay in event-time order
  3. measure latency-to-alert and false-positive bursts.

---

## 12) Naming Clarification

- File name is **`upd_flood.csv`** exactly as requested.
- Attack label inside rows is **`udp_flood`** (standard taxonomy-aligned naming).
