# Cybersecurity Agent Microservice

A comprehensive multi-agent cybersecurity system built with LangGraph, FastAPI, and Kafka for real-time threat detection, intrusion response, and security reporting.

## 🚀 Features

- **Multi-Agent Architecture**: 4 specialized AI agents working in coordination
- **Real-time Processing**: Kafka-based event streaming for immediate threat response
- **LLM-Powered Analysis**: Groq integration for intelligent security assessment
- **Comprehensive Monitoring**: Prometheus and Grafana integration
- **RESTful API**: FastAPI-based endpoints for all security operations
- **Docker Containerized**: Easy deployment and scaling

## 🏗 Architecture

### Agent Overview
1. **Data Integrity Agent**: Validates sensor data, detects tampering, verifies checksums
2. **Threat Detection Agent**: Analyzes security events, identifies attack patterns
3. **Intrusion Response Agent**: Monitors network traffic, responds to suspicious activities
4. **Reporting Agent**: Generates comprehensive security reports and alerts

### Technology Stack
- **Framework**: FastAPI + LangGraph
- **LLM Provider**: Groq (Llama 3)
- **Message Broker**: Apache Kafka
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- Groq API key ([Get it here](https://console.groq.com/))
- Windows/Linux/macOS platform support

## 🔧 Quick Start

### 1. Clone and Setup
```bash
cd cybersecurity-agent
```

### 2. Configure Environment
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check service health
curl http://localhost:8000/health

# View logs
docker-compose logs -f cybersecurity-agent
```

## 🌐 Service Endpoints

### Core Analysis
- `POST /analyze/security` - Full multi-agent security analysis
- `POST /analyze/integrity` - Data integrity validation
- `POST /analyze/threats` - Threat detection analysis  
- `POST /respond/intrusion` - Intrusion response coordination
- `POST /reports/generate` - Generate security reports

### Event Publishing
- `POST /events/threat` - Publish threat alerts
- `POST /events/network` - Publish network events
- `POST /events/batch` - Batch event publishing

### Monitoring & Status
- `GET /health` - Service health check
- `GET /status/agents` - Agent status overview
- `GET /status/kafka` - Kafka connection status
- `GET /metrics/security` - Security metrics

### Emergency Response
- `POST /emergency/analysis` - Trigger emergency security analysis

## 📊 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Cybersecurity API** | http://localhost:8000 | - |
| **API Documentation** | http://localhost:8000/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin/admin123 |

## 🔄 Kafka Topics

The system automatically creates and manages these topics:

- `cyber_alerts` - Security alerts and notifications
- `sensor_data` - IoT sensor data streams
- `network_events` - Network traffic events
- `security_incidents` - Security incident reports
- `incident_reports` - Detailed incident documentation
- `executive_reports` - Executive summary reports
- `rag_knowledge_updates` - Knowledge base updates

## 💡 Usage Examples

### Trigger Security Analysis
```bash
curl -X POST "http://localhost:8000/analyze/security" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "full",
    "time_window": 300,
    "priority": "high"
  }'
```

### Publish Threat Alert
```bash
curl -X POST "http://localhost:8000/events/threat" \
  -H "Content-Type: application/json" \
  -d '{
    "threat_type": "malware",
    "confidence": "high",
    "source_ip": "192.168.1.100",
    "details": {"attack_vector": "phishing"}
  }'
```

### Check Data Integrity
```bash
curl -X POST "http://localhost:8000/analyze/integrity" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "sensor_001",
    "time_window": 600
  }'
```

## 🔍 Monitoring & Observability

### Prometheus Metrics
- Agent execution times and success rates
- Kafka message processing metrics
- Threat detection statistics
- System health indicators

### Grafana Dashboards
- Real-time security event monitoring
- Agent performance metrics
- Threat landscape visualization
- System resource utilization

### Log Analysis
```bash
# View agent-specific logs
docker-compose logs -f cybersecurity

# Monitor Kafka logs
docker-compose logs -f kafka

# Check all services
docker-compose logs --tail=100
```

## ⚙️ Configuration

### Environment Variables
```env
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (with defaults)
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_CONSUMER_GROUP=cybersecurity_agents
LOG_LEVEL=INFO
GROQ_MODEL=llama3-8b-8192
GROQ_TEMPERATURE=0.1
```

### Agent Configuration
Key settings in `src/config/settings.py`:
- **Risk Thresholds**: Customizable threat severity levels
- **Timeouts**: Agent execution and retry settings
- **Data Validation**: Integrity check parameters
- **Network Monitoring**: Traffic analysis configurations

## 🔒 Security Features

### Data Integrity
- Checksum validation for all sensor data
- Tampering detection algorithms
- Data corruption identification
- Source verification protocols

### Threat Detection
- Real-time event analysis
- Pattern recognition for attack vectors
- Multi-source correlation
- Confidence scoring for threats

### Intrusion Response
- Network traffic monitoring
- Suspicious IP identification
- Automated response actions
- Risk assessment and prioritization

### Comprehensive Reporting
- Executive summaries
- Detailed incident reports
- Trend analysis
- Actionable recommendations

## 🚦 Operational Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart cybersecurity-agent
```

### Health Monitoring
```bash
# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# View service health
curl http://localhost:8000/health | jq
```

### Troubleshooting
```bash
# Check agent logs
docker-compose logs cybersecurity-agent

# Verify Kafka connectivity
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Test API endpoints
curl http://localhost:8000/docs
```

## 📈 Performance & Scaling

### Resource Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended  
- **Storage**: 10GB for logs and data
- **Network**: Stable internet for LLM API calls

### Scaling Options
```bash
# Scale agent instances
docker-compose up -d --scale cybersecurity-agent=3

# Monitor performance
docker-compose exec prometheus curl localhost:9090/api/v1/query?query=up
```

## 🔧 Development

### Project Structure
```
cybersecurity/
├── src/
│   ├── agents/           # Individual agent implementations
│   ├── graph/           # Multi-agent coordination
│   ├── kafka/           # Kafka integration
│   ├── config/          # Configuration management
│   └── main.py          # FastAPI application
├── Dockerfile           # Container definition
└── requirements.txt     # Python dependencies
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key

# Run locally
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation with:
- Complete endpoint listings
- Request/response schemas
- Interactive testing interface
- Authentication requirements
- Example payloads

## 🎯 Use Cases

### Smart Building Security
- IoT sensor integrity monitoring
- Network intrusion detection
- Automated threat response
- Security compliance reporting

### Industrial IoT Protection  
- Manufacturing system security
- Supply chain threat detection
- Critical infrastructure protection
- Real-time incident response

### Enterprise Security Operations
- Multi-source threat intelligence
- Automated security analysis
- Executive security reporting
- Compliance monitoring

---

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs cybersecurity-agent`
2. Verify configuration in `.env` and `settings.py`
3. Test API endpoints at `http://localhost:8000/docs`
4. Monitor services at `http://localhost:3001` (Grafana)