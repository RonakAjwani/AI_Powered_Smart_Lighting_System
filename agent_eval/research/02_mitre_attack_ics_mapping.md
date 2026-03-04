# MITRE ATT&CK for ICS — TTP Mapping for Smart Lighting Scenarios

## Why ATT&CK for ICS (not Enterprise)?

Smart lighting in commercial/city infrastructure is classified as **Operational Technology (OT)**, making the ICS matrix more appropriate. Smart lighting integrated into building automation presents similar attack surfaces to SCADA/ICS systems.

## Complete TTP Reference

### Initial Access Techniques

| Technique | ID | Relevance to Smart Lighting |
|---|---|---|
| Internet Accessible Device | T0883 | Smart lighting APIs exposed to internet |
| Default Credentials | T0882 | IoT devices with factory passwords |
| Wireless Compromise | T0888 | Zigbee/LoRa/Wi-Fi mesh exploitation |
| Supply Chain Compromise | T0862 | Malware in firmware during manufacturing |
| Exploitation of Remote Services | T0870 | Vulnerabilities in lighting control APIs |

### Execution Techniques

| Technique | ID | Relevance |
|---|---|---|
| Change Program State | T0875 | Firmware modification, malware installation |
| Unauthorized Command Message | T0804 | Rogue lighting control commands |

### Command & Control Techniques

| Technique | ID | Relevance |
|---|---|---|
| Standard Application Layer Protocol | T0869 | C2 over HTTP/HTTPS |
| Connection Proxy | T0881 | Botnet proxy routing |

### Impact Techniques

| Technique | ID | Relevance |
|---|---|---|
| Denial of Control | T0813 | DDoS preventing operator control |
| Loss of Productivity and Revenue | T0834 | Service disruption |
| Manipulation of Control | T0831 | Unauthorized lighting changes |

## TTP-to-Scenario Mapping

| Scenario | Kill Chain Phase | TTPs Used |
|---|---|---|
| **S2**: HTTP Flood on BKC | Initial Access → Impact | T0883 → T0804 → T0813 |
| **S3**: SYN Flood on Hospital | Initial Access → Impact | T0883 → T0813, T0834 |
| **S4**: Volumetric on Airport | Execution → Impact | T0804 → T0813, T0834 |
| **S5**: Slowloris on Port | Initial Access → Impact | T0883 → T0813 |
| **S6**: DNS Amp on School | Execution → Impact | T0804 → T0813 |
| **S7**: Multi-vector on Residential | All phases | T0883 → T0804 → T0813 |
| **M1**: IoT Botnet on Highway | All phases | T0882 → T0875 → T0869 → T0813 |
| **M2**: Ransomware on Hospital | Initial Access → Impact | T0883 → T0875 → T0834 |
| **M3**: Firmware Rootkit on Airport | Supply Chain → Impact | T0862 → T0875 → T0831 |
| **M4**: Cryptominer on Residential | Initial Access → Execution | T0882 → T0875 |

## Mirai Botnet TTP Chain (Reference for M1)

1. **Scanning/Reconnaissance** (T0846): Identifying vulnerable IoT devices
2. **Default Credentials** (T0882): Brute-forcing with common IoT passwords
3. **Change Program State** (T0875): Installing botnet malware
4. **Standard App Protocol** (T0869): C2 beacon via HTTP
5. **Denial of Control** (T0813): Launching DDoS from compromised fleet

## References
- MITRE ATT&CK for ICS: https://attack.mitre.org/techniques/ics/
- Mirai Botnet Analysis (Trend Micro): https://www.trendmicro.com/en_us/research.html
- Forescout IoT Threat Research: https://www.forescout.com/research/
