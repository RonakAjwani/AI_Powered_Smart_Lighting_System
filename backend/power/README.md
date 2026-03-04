# Power Grid Management Agent Microservice

A comprehensive multi-agent power grid management system built with LangGraph, FastAPI, and Kafka for real-time energy optimization, load forecasting, outage detection, and grid reporting.

## 🚀 Features

- **Multi-Agent Architecture**: 5 specialized AI agents working in coordination
- **Real-time Grid Management**: Kafka-based event streaming for immediate response
- **LLM-Powered Analysis**: Groq integration for intelligent grid optimization
- **Predictive Analytics**: Advanced load forecasting and trend analysis
- **Emergency Response**: Automated outage detection and energy rerouting
- **RESTful API**: FastAPI-based endpoints for all power grid operations
- **Docker Containerized**: Easy deployment and scaling

## 🏗 Architecture

### Agent Overview
1. **Energy Load Forecaster Agent**: Predicts energy demand, analyzes consumption patterns
2. **Power Outage Detection Agent**: Monitors grid health, detects outages and failures
3. **Energy Rerouting Agent**: Manages energy flow, activates backup systems
4. **Energy Optimization Agent**: Optimizes consumption, implements energy savings
5. **Power Grid Reporting Agent**: Generates comprehensive grid reports and analytics

### Technology Stack
- **Framework**: FastAPI + LangGraph
- **LLM Provider**: Groq (Llama 3)
- **Message Broker**: Apache Kafka
- **Workflow Engine**: LangGraph with memory persistence
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- Groq API key ([Get it here](https://console.groq.com/))
- Windows/Linux/macOS platform support

## 🔧 Quick Start

### 1. Clone and Setup
```bash
cd power
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
curl http://localhost:8002/health

# View logs
docker-compose logs -f power-agent
```

## 🌐 Service Endpoints

### Workflow Management
- `POST /workflow/execute` - Execute complete power grid workflow
- `GET /workflow/status/{workflow_id}` - Get workflow status
- `GET /workflow/active` - List active workflows
- `GET /workflow/history` - Get workflow history

### Emergency Response
- `POST /emergency/trigger` - Trigger emergency procedures

### Individual Agents
- `POST /agents/forecast` - Energy load forecasting
- `POST /agents/detect-outages` - Power outage detection
- `POST /agents/reroute-energy` - Energy rerouting operations
- `POST /agents/optimize-energy` - Energy optimization
- `POST /agents/generate-reports` - Grid report generation

### System Management
- `GET /health` - Service health check
- `GET /system/status` - Comprehensive system status
- `GET /system/metrics` - Performance metrics
- `GET /config` - Service configuration

## 📊 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Power Grid API** | http://localhost:8002 | - |
| **API Documentation** | http://localhost:8002/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3002 | admin/admin123 |

## 🔄 Kafka Topics

The system automatically creates and manages these topics:

- `power_forecasts` - Energy demand forecasting data
- `power_outages` - Outage alerts and notifications
- `power_optimization` - Energy optimization commands
- `power_reports` - Grid performance reports
- `grid_status_updates` - Real-time grid status changes
- `energy_commands` - System control commands
- `backup_activations` - Backup power system events
- `load_shedding_events` - Emergency load shedding notifications

## 💡 Usage Examples

### Execute Complete Grid Workflow
```bash
curl -X POST "http://localhost:8002/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_type": "manual",
    "description": "Comprehensive grid analysis",
    "config_overrides": {"optimization_needed": true}
  }'
```

### Trigger Emergency Response
```bash
curl -X POST "http://localhost:8002/emergency/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "emergency_type": "grid_failure",
    "affected_zones": ["zone_1", "zone_2"],
    "severity": "critical",
    "description": "Major grid failure in downtown area"
  }'
```

### Generate Load Forecast
```bash
curl -X POST "http://localhost:8002/agents/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "periods": ["1_hour", "24_hour", "weekly"],
    "include_weather": true,
    "include_historical": true
  }'
```

### Check Workflow Status
```bash
curl "http://localhost:8002/workflow/status/power_grid_20241021_143022"
```

## 🔍 Monitoring & Observability

### Key Metrics
- Energy load forecasting accuracy
- Outage detection response time
- Energy optimization savings achieved
- Grid reliability metrics (SAIDI, SAIFI, CAIDI)
- System availability and uptime

### Performance Dashboards
- Real-time energy consumption monitoring
- Grid health and reliability metrics
- Agent performance and execution times
- Cost analysis and optimization results

### Log Analysis
```bash
# View power grid logs
docker-compose logs -f power-agent

# Monitor specific agent activity
docker-compose logs -f power-agent | grep "Energy Optimization"

# Check workflow execution
docker-compose logs --tail=100 power-agent | grep "workflow"
```

## ⚙️ Configuration

### Environment Variables
```env
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (with defaults)
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_CONSUMER_GROUP=power_grid_agents
LOG_LEVEL=INFO
GROQ_MODEL=llama3-8b-8192
GROQ_TEMPERATURE=0.1
ENERGY_SAVINGS_TARGET=15.0
RELIABILITY_TARGET=99.5
EFFICIENCY_BASELINE=95.0
```

### Grid Configuration
Key settings in `src/config/settings.py`:
- **Zone Management**: Default zones and priority zones
- **Performance Targets**: Energy savings, reliability, and efficiency goals
- **Alert Thresholds**: Peak load, budget, and outage alert levels
- **Optimization Parameters**: Dimming limits and scheduling constraints

## ⚡ Power Grid Features

### Energy Load Forecasting
- Multi-period demand prediction (1h, 4h, 24h, weekly)
- Weather integration for accurate forecasting
- Historical pattern analysis
- Confidence scoring and trend analysis

### Power Outage Detection
- Real-time grid health monitoring
- Voltage and frequency stability analysis
- Automated outage classification
- Risk assessment and impact analysis

### Energy Rerouting
- Automatic backup power activation
- Load shedding coordination
- Energy flow optimization
- Emergency response procedures

### Energy Optimization
- Smart dimming algorithms
- Schedule optimization
- Peak demand management
- Cost reduction strategies

### Comprehensive Reporting
- Executive dashboards
- Performance analytics
- Financial analysis
- Predictive maintenance recommendations

## 🚦 Operational Commands

### Workflow Management
```bash
# Execute scheduled workflow
curl -X POST "http://localhost:8002/workflow/execute" \
  -d '{"trigger_type": "scheduled"}'

# Check active workflows
curl "http://localhost:8002/workflow/active"

# View workflow history
curl "http://localhost:8002/workflow/history?limit=5"
```

### Emergency Operations
```bash
# Trigger grid emergency
curl -X POST "http://localhost:8002/emergency/trigger" \
  -d '{
    "emergency_type": "widespread_outage",
    "affected_zones": ["zone_1", "zone_2", "zone_3"],
    "severity": "critical"
  }'
```

### Individual Agent Operations
```bash
# Run outage detection
curl -X POST "http://localhost:8002/agents/detect-outages"

# Execute energy optimization
curl -X POST "http://localhost:8002/agents/optimize-energy" \
  -d '{"priority_mode": "max_savings"}'

# Generate reports
curl -X POST "http://localhost:8002/agents/generate-reports" \
  -d '{"report_type": "comprehensive"}'
```

## 📈 Performance & Scaling

### Resource Requirements
- **CPU**: 4+ cores recommended for multi-agent workflows
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB for logs, reports, and workflow data
- **Network**: Stable internet for LLM API calls and Kafka messaging

### Scaling Options
```bash
# Scale power grid instances
docker-compose up -d --scale power-agent=2

# Monitor system resources
docker stats power-agent

# Check agent performance
curl "http://localhost:8002/system/metrics"
```

## 🔧 Development

### Project Structure
```
power/
├── src/
│   ├── agents/          # Individual agent implementations
│   │   ├── energy_load_forecaster_agent.py
│   │   ├── power_outage_detection_agent.py
│   │   ├── energy_rerouting_agent.py
│   │   ├── energy_optimization_agent.py
│   │   └── power_grid_reporting_agent.py
│   ├── graph/           # Multi-agent orchestration
│   │   └── power_graph.py
│   ├── kafka/           # Kafka integration
│   ├── config/          # Configuration management
│   └── main.py          # FastAPI application
├── tests/               # Comprehensive test suite
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
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific agent tests
pytest tests/test_agent.py::TestEnergyLoadForecasterAgent -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📚 API Documentation

Once running, visit `http://localhost:8002/docs` for interactive API documentation with:
- Complete endpoint listings
- Request/response schemas
- Interactive testing interface
- Workflow execution examples
- Agent-specific operations

## 🎯 Use Cases

### Smart City Power Management
- Municipal energy optimization
- Street lighting automation
- Peak demand management
- Emergency response coordination

### Industrial Energy Management
- Manufacturing power optimization
- Backup system coordination
- Energy cost reduction
- Reliability improvement

### Commercial Building Operations
- Office building energy optimization
- HVAC coordination with lighting
- Demand response programs
- Sustainability reporting

### Emergency Response
- Natural disaster power coordination
- Critical facility backup management
- Public safety lighting maintenance
- Recovery planning and execution

## 📊 Grid Performance Metrics

### Reliability Metrics
- **SAIDI** (System Average Interruption Duration Index)
- **SAIFI** (System Average Interruption Frequency Index)
- **CAIDI** (Customer Average Interruption Duration Index)
- **System Availability** percentage

### Efficiency Metrics
- **Energy Savings** achieved vs target
- **Peak Load Reduction** percentage
- **Power Factor** optimization
- **Transmission Efficiency** improvement

### Financial Metrics
- **Cost per kWh** analysis
- **Monthly Budget** performance
- **ROI** on optimization measures
- **Demand Charge** optimization

## 🔄 Workflow Examples

### Normal Operations Workflow
1. **Load Forecasting** → Predict energy demand
2. **Outage Detection** → Monitor grid health
3. **Energy Optimization** → Implement savings
4. **Report Generation** → Analytics and insights

### Emergency Response Workflow
1. **Outage Detection** → Identify critical failures
2. **Emergency Assessment** → Classify severity
3. **Energy Rerouting** → Activate backup systems
4. **Emergency Reporting** → Stakeholder notifications

### Scheduled Maintenance Workflow
1. **Load Forecasting** → Plan maintenance windows
2. **Energy Rerouting** → Prepare backup systems
3. **Optimization** → Minimize impact
4. **Reporting** → Track maintenance effectiveness

---

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs power-agent`
2. Verify configuration in `.env` and `settings.py`
3. Test API endpoints at `http://localhost:8002/docs`
4. Monitor workflows at `http://localhost:8002/workflow/active`
5. Check system status at `http://localhost:8002/system/status`

## 🔗 Integration

The Power Grid Management Service integrates seamlessly with:
- **Smart Lighting System** - Coordinated energy optimization
- **Weather Service** - Weather-based load forecasting
- **Cybersecurity Service** - Secure grid operations
- **IoT Sensors** - Real-time grid monitoring
- **Building Management Systems** - Facility coordination

---

**Ready to power your smart grid operations with AI-driven intelligence! ⚡🤖**