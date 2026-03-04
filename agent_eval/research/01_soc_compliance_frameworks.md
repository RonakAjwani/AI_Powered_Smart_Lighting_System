# SOC Compliance & Cybersecurity Frameworks for Smart Lighting

## 1. SOC (Security Operations Center) — Tier Mapping

### SOC Tiers & AI Agent Mapping

| SOC Tier | Human Role | Our AI Agent | Function |
|---|---|---|---|
| **Tier 1** | Alert Monitoring & Triage | `LogIngestionAgent` + `TriageAgent` | Continuous log collection, initial alert classification, false positive filtering |
| **Tier 2** | Deep Investigation | `DDoSDetectionAgent` + `MalwareDetectionAgent` | Pattern analysis, LLM-based threat detection, severity assessment |
| **Tier 3** | Threat Hunting & Response | `IncidentResponseAgent` | Correlation, mitigation playbook execution, containment actions |
| **SOC Manager** | Reporting & Compliance | `ReportingAgent` | NIST/MITRE-mapped incident reports, compliance documentation |

**Research finding**: AI is flattening traditional SOC tier structures. Studies show AI agents can reduce Tier 1 investigation time from 25-40 minutes to ~3 minutes while maintaining consistent SOP adherence.

### SOC 2 Trust Service Criteria Mapping

| TSC | Criteria | How Our Arena Tests It |
|---|---|---|
| **Security** | Protection against unauthorized access | DDoS/malware detection accuracy |
| **Availability** | System available for operation | Service uptime during attacks |
| **Processing Integrity** | Processing is complete, valid, accurate | Agent detection accuracy, FP rate |
| **Confidentiality** | Confidential info protected | Data exfiltration detection |
| **Privacy** | Personal info handling | Not directly applicable (IoT grid) |

---

## 2. NIST Frameworks

### NIST Cybersecurity Framework (CSF) — Agent Mapping

| CSF Function | Our Agent | Specific Activities |
|---|---|---|
| **Identify** | LogIngestionAgent | Asset inventory, zone discovery, device cataloging |
| **Protect** | TriageAgent | Policy enforcement, access control decisions |
| **Detect** | DDoSDetectionAgent, MalwareDetectionAgent | Anomaly detection, continuous monitoring |
| **Respond** | IncidentResponseAgent | Containment, mitigation playbooks, IP blocking |
| **Recover** | ReportingAgent + IncidentResponseAgent | Service restoration, lessons learned |

### NIST SP 800-213 (IoT Device Cybersecurity)
- Device identification and authentication
- Software/firmware update capability
- Event logging and monitoring
- Data protection (at rest and in transit)

### NIST SP 800-183 (Networks of Things) — IoT Primitives

| NIST Primitive | Arena Component |
|---|---|
| **Sensor** | Smart lighting controllers in each zone |
| **Aggregator** | LogIngestionAgent (collects and normalizes) |
| **Communication Channel** | Kafka/Redpanda message bus |
| **eUtility** | LLM-powered analysis agents |
| **Decision Trigger** | IncidentResponseAgent (takes action) |

---

## 3. IEC 62443 (Industrial Cybersecurity) — Security Levels

| Zone | Criticality | IEC 62443 SL | Justification |
|---|---|---|---|
| BKC Commercial | High | SL-3 | Financial impact, high traffic |
| Reliance Hospital | Critical | SL-4 | Human safety, medical equipment |
| Airport | Critical | SL-4 | National infrastructure |
| Port Area | High | SL-3 | Trade/logistics |
| School Complex | Medium | SL-2 | Public safety |
| Residential | Medium | SL-2 | Quality of life |
| Highway Corridor | High | SL-3 | Traffic safety |

**Key insight**: Agents should apply stricter detection thresholds for SL-4 zones (hospital, airport) than SL-2 zones.

---

## References
- NIST Cybersecurity Framework (CSF): https://www.nist.gov/cyberframework
- NIST SP 800-213 (IoT Device Cybersecurity): https://csrc.nist.gov/publications/detail/sp/800-213/final
- NIST SP 800-183 (Networks of Things): https://csrc.nist.gov/publications/detail/sp/800-183/final
- IEC 62443: https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards
- SOC 2 Trust Service Criteria: https://www.aicpa.org/soc
