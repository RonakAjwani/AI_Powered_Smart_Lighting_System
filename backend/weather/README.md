# Weather Intelligence Agent Microservice

A comprehensive multi-agent weather intelligence system built with LangGraph, FastAPI, and Kafka for real-time weather monitoring, impact analysis, and smart lighting optimization.

## 🚀 Features

- **Multi-Agent Architecture**: 5 specialized AI agents working in coordination
- **Real-time Weather Processing**: Kafka-based event streaming for immediate response
- **LLM-Powered Analysis**: Groq integration for intelligent weather assessment
- **Emergency Response**: Automated disaster response and evacuation protocols
- **Comprehensive Forecasting**: Multi-zone weather prediction and impact analysis
- **RESTful API**: FastAPI-based endpoints for all weather operations
- **Docker Containerized**: Easy deployment and scaling

## 🏗 Architecture

### Agent Overview
1. **Weather Collection & Forecast Agent**: Collects real-time weather data, generates forecasts
2. **Environmental Sensor Agent**: Monitors air quality, noise, and environmental conditions
3. **Weather Impact Analyzer Agent**: Analyzes weather effects on lighting requirements
4. **Disaster Response Advisor Agent**: Coordinates emergency responses and evacuation protocols
5. **Reporting Agent**: Generates comprehensive weather reports and analytics

### Technology Stack
- **Framework**: FastAPI + LangGraph
- **LLM Provider**: Groq (Llama 3)
- **Weather APIs**: OpenWeather API
- **Message Broker**: Apache Kafka
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- Groq API key ([Get it here](https://console.groq.com/))
- OpenWeather API key ([Get it here](https://openweathermap.org/api))
- Windows/Linux/macOS platform support

## 🔧 Quick Start

### 1. Clone and Setup
```bash
cd weather
```

### 2. Configure Environment
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check service health
curl http://localhost:8001/health

# View logs
docker-compose logs -f weather-service
```

## 🌐 Service Endpoints

### Core Weather Intelligence
- `POST /weather/execute` - Full multi-agent weather intelligence
- `GET /weather/status` - Weather system status overview
- `GET /weather/data/current` - Current weather data for all zones
- `GET /weather/forecast/{zone_id}` - Weather forecast for specific zone
- `GET /weather/alerts` - Current weather alerts

### Individual Agent Execution
- `POST /weather/agents/collection/execute` - Weather data collection
- `POST /weather/agents/sensor/execute` - Environmental sensor monitoring
- `POST /weather/agents/impact/execute` - Weather impact analysis
- `POST /weather/agents/disaster/execute` - Disaster response coordination
- `POST /weather/agents/reporting/execute` - Weather reporting

### Emergency Response
- `POST /weather/emergency/activate` - Activate emergency weather mode
- `GET /weather/analytics/performance` - System performance analytics
- `GET /weather/analytics/forecast-accuracy` - Forecast accuracy metrics

### Configuration & Control
- `GET /weather/config` - Weather system configuration
- `POST /weather/config/update` - Update system configuration
- `WS /weather/ws` - Real-time weather updates WebSocket

## 📊 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Weather Intelligence API** | http://localhost:8001 | - |
| **API Documentation** | http://localhost:8001/docs | - |
| **Prometheus** | http://localhost:9091 | - |
| **Grafana** | http://localhost:3002 | admin/weather_admin |
| **Kafka UI** | http://localhost:8080 | - |

## 🔄 Kafka Topics

The system automatically creates and manages these topics:

- `weather_alerts` - Weather alerts and warnings
- `weather_data` - Real-time weather data streams
- `weather_forecasts` - Weather forecast updates
- `weather_reports` - Generated weather reports
- `weather_emergency` - Emergency weather notifications

## 💡 Usage Examples

### Execute Complete Weather Intelligence
```bash
curl -X POST "http://localhost:8001/weather/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_mode": "auto"
  }'
```

### Get Current Weather Data
```bash
curl -X GET "http://localhost:8001/weather/data/current"
```

### Get Zone-Specific Forecast
```bash
curl -X GET "http://localhost:8001/weather/forecast/zone_1?hours=24"
```

### Activate Emergency Mode
```bash
curl -X POST "http://localhost:8001/weather/emergency/activate"
```

### WebSocket Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8001/weather/ws');
ws.onmessage = function(event) {
    const weatherUpdate = JSON.parse(event.data);
    console.log('Weather update:', weatherUpdate);
};
```

## 🔍 Monitoring & Observability

### Prometheus Metrics
- Agent execution times and success rates
- Weather data collection metrics
- Forecast accuracy statistics
- Emergency response metrics

### Grafana Dashboards
- Real-time weather monitoring
- Agent performance visualization
- Weather alert tracking
- System resource utilization

### Log Analysis
```bash
# View weather service logs
docker-compose logs -f weather-service

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
OPENWEATHER_API_KEY=your_openweather_api_key

# Optional (with defaults)
WEATHER_PORT=8001
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
LOG_LEVEL=INFO
GROQ_MODEL=llama3-8b-8192
GROQ_TEMPERATURE=0.1
```

### Weather Configuration
Key settings in `src/config/settings.py`:
- **Zone Coordinates**: Geographic locations for weather monitoring
- **Weather Thresholds**: Customizable alert levels
- **Update Intervals**: Data collection frequencies
- **Emergency Thresholds**: Critical weather condition triggers

## 🌦️ Weather Features

### Real-time Data Collection
- Multi-zone weather monitoring
- OpenWeather API integration
- Environmental sensor data
- Air quality measurements

### Intelligent Forecasting
- 48-hour weather predictions
- Zone-specific forecasts
- Accuracy tracking and improvement
- Confidence scoring

### Impact Analysis
- Lighting requirement adjustments
- Weather effect calculations
- Risk assessment
- Performance optimization

### Emergency Response
- Severe weather detection
- Automated alert generation
- Evacuation protocol activation
- Emergency lighting coordination

### Comprehensive Reporting
- Daily weather summaries
- Forecast accuracy reports
- Performance analytics
- Trend analysis

## 🚦 Operational Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart weather service
docker-compose restart weather-service
```

### Health Monitoring
```bash
# Check service status
docker-compose ps

# Monitor resource usage
docker stats

# View service health
curl http://localhost:8001/health | jq
```

### Troubleshooting
```bash
# Check weather service logs
docker-compose logs weather-service

# Verify Kafka connectivity
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Test API endpoints
curl http://localhost:8001/docs
```

## 📈 Performance & Scaling

### Resource Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for logs and weather data
- **Network**: Stable internet for weather API calls

### Scaling Options
```bash
# Scale weather service instances
docker-compose up -d --scale weather-service=3

# Monitor performance
docker-compose exec prometheus curl localhost:9090/api/v1/query?query=up
```

## 🔧 Development

### Project Structure
```
weather/
├── src/
│   ├── weather_agents/      # Individual agent implementations
│   ├── config/             # Configuration management
│   ├── kafka/              # Kafka integration
│   └── main.py             # FastAPI application
├── tests/
│   └── test_agent.py       # Comprehensive test suite
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key
export OPENWEATHER_API_KEY=your_weather_key

# Run locally
python main.py
```

## 📚 API Documentation

Once running, visit `http://localhost:8001/docs` for interactive API documentation with:
- Complete endpoint listings
- Request/response schemas
- Interactive testing interface
- Weather data models
- Example payloads

## 🎯 Use Cases

### Smart Lighting Optimization
- Weather-based lighting adjustments
- Energy efficiency optimization
- Visibility enhancement
- Safety lighting automation

### Emergency Management
- Severe weather response
- Evacuation coordination
- Emergency lighting protocols
- Public safety alerts

### Environmental Monitoring
- Air quality tracking
- Weather pattern analysis
- Climate condition assessment
- Environmental impact reporting

### Predictive Analytics
- Weather forecasting
- Impact prediction
- Performance optimization
- Resource planning

## 🌍 Zone Configuration

The system supports multiple monitoring zones with customizable coordinates:

```json
{
  "zone_1": {"lat": 40.7128, "lon": -74.0060},
  "zone_2": {"lat": 40.7589, "lon": -73.9851},
  "zone_3": {"lat": 40.6892, "lon": -74.0445},
  "zone_4": {"lat": 40.7831, "lon": -73.9712},
  "zone_5": {"lat": 40.7282, "lon": -73.7949}
}
```

## 🎛️ Weather Thresholds

### Normal Operation Thresholds
- **Visibility**: < 1000m triggers enhanced lighting
- **Wind Speed**: > 15 m/s activates wind protocols
- **Precipitation**: > 5 mm/h increases lighting intensity

### Emergency Thresholds
- **Wind Speed**: > 25 m/s triggers emergency mode
- **Precipitation**: > 20 mm/h activates flood protocols
- **Temperature**: < -10°C or > 35°C extreme weather response

---

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs weather-service`
2. Verify configuration in `.env` and `settings.py`
3. Test API endpoints at `http://localhost:8001/docs`
4. Monitor services at `http://localhost:3002` (Grafana)
5. View Kafka topics at `http://localhost:8080` (Kafka UI)