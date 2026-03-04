# Docker vs Network Simulators for IoT Grid Simulation

## Comparison Matrix

| Tool | Type | Resource Cost | Network Realism | Application Realism | Best For |
|---|---|---|---|---|---|
| **Docker** | Application emulation | Low (~50MB/zone) | Topology only | Full application stack | Agent evaluation, API testing |
| **NS-3** | Discrete-event simulator | High (2-3GB) | Packet-level | Limited | Protocol analysis, PHY/MAC |
| **Mininet/Containernet** | SDN emulator + Docker | Medium (~500MB+) | SDN topology | Docker containers | SDN research |
| **GNS3** | Full network emulator | Very High (4GB+) | Real network OS | VMs/Docker | Network certification |
| **CORE** | Network emulator | Medium | Link-layer | Linux containers | Military/govt research |

## Why Docker is the Right Choice for This Project

1. **Scope match**: We're evaluating *agent intelligence*, not protocol correctness
2. **Academic validation**: CMU research validates Docker+Kafka for IoT simulation (SciTePress, 2024)
3. **Resource efficiency**: Each zone container uses ~50MB vs GNS3's 4GB+
4. **Reproducibility**: Docker Compose provides deterministic, version-controlled environments
5. **Future upgrade**: Can add Containernet (Mininet fork with Docker) for SDN if needed

## Docker Grid Topology Design

Each zone = 1 Docker container running lightweight Python process simulating:
- N smart poles (configurable per zone based on real layout)
- Gateways aggregating pole data (simulates mesh network)
- Zone controller publishing aggregated events to message bus
- Realistic traffic patterns (diurnal cycle, zone-specific profiles)

## Real Smart Lighting Grid Architecture (Reference)

A real Mumbai smart lighting grid has:
- **Zone controllers**: Per-zone gateway managing 50-200 lights
- **Smart poles**: Individual poles with sensors (ambient light, motion, power meter)
- **Communication**: Mesh network (Zigbee/LoRa) within zones, IP backbone between zones
- **Central management**: Cloud/on-prem server for fleet management
- **Protocols**: DALI (Digital Addressable Lighting Interface), Zigbee, LoRa, MQTT

## References
- CMU Docker+NS-3 IoT Simulation: https://www.cmu.edu/
- Containernet (Mininet + Docker): https://containernet.github.io/
- Docker IoT Testbeds (SciTePress, 2024): https://www.scitepress.org/
