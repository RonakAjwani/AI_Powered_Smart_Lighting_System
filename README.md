# AI-Powered Smart Lighting System

A comprehensive multi-agent AI system for intelligent lighting management with cybersecurity, weather intelligence, and power grid optimization.

## 🌟 System Overview

This smart lighting ecosystem consists of three specialized AI agent services that work together to provide secure, weather-adaptive, and energy-efficient lighting management for smart cities, buildings, and infrastructure.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Cybersecurity  │    │    Weather      │    │   Power Grid    │
│     Service     │    │  Intelligence   │    │   Management    │
│    (Port 8003)  │    │   (Port 8001)   │    │   (Port 8002)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │   Shared Infrastructure │
                    │  Kafka • Redis • DB     │
                    │ Prometheus • Grafana    │
                    └─────────────────────────┘
```

## 🚀 Services

### 🛡️ Cybersecurity Service
**Protects your lighting infrastructure from cyber threats**

- **Real-time threat detection** and automated response
- **Vulnerability assessment** and security monitoring  
- **Incident response** with immediate threat mitigation
- **Security reporting** and compliance documentation

**Key Capabilities**: Network monitoring, intrusion detection, automated security responses, vulnerability scanning

---

### 🌤️ Weather Intelligence Service  
**Optimizes lighting based on weather and environmental conditions**

- **Weather-based automation** for optimal lighting control
- **Daylight analysis** and seasonal adjustments
- **Energy optimization** through weather prediction
- **Environmental impact** assessment and reporting

**Key Capabilities**: Real-time weather integration, smart dimming, seasonal scheduling, energy savings

---

### ⚡ Power Grid Management Service
**Manages energy consumption and grid reliability**

- **Load forecasting** and demand prediction
- **Outage detection** and automated rerouting
- **Energy optimization** and cost reduction
- **Grid reliability** monitoring and reporting

**Key Capabilities**: Predictive analytics, backup power management, energy efficiency, grid stability

## 🔄 Integration Features

- **Cross-Service Communication**: Kafka-based real-time messaging
- **Unified Monitoring**: Prometheus metrics and Grafana dashboards
- **Shared Data Layer**: PostgreSQL database and Redis caching
- **Coordinated Operations**: Services work together for optimal performance

## 📊 Monitoring & Observability

| Service | API Docs | Monitoring Dashboard |
|---------|----------|---------------------|
| **Cybersecurity** | http://localhost:8003/docs | http://localhost:3000 |
| **Weather Intelligence** | http://localhost:8001/docs | http://localhost:3001 |
| **Power Grid Management** | http://localhost:8002/docs | http://localhost:3002 |

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Groq API key
- OpenWeather API key (for weather service)

### 1. Environment Setup
```bash
# Create .env file
GROQ_API_KEY=your_groq_api_key
OPENWEATHER_API_KEY=your_openweather_key
```

### 2. Deploy All Services
```bash
# Start the complete ecosystem
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### 3. Access Services
```bash
# Check system health
curl http://localhost:8003/health  # Cybersecurity
curl http://localhost:8001/health  # Weather
curl http://localhost:8002/health  # Power Grid

# View API documentation
open http://localhost:8003/docs    # Cybersecurity API
open http://localhost:8001/docs    # Weather API  
open http://localhost:8002/docs    # Power Grid API
```

## 🎯 Use Cases

### Smart City Deployment
- **Municipal lighting** with weather adaptation
- **Security monitoring** for public infrastructure
- **Energy optimization** for cost savings
- **Emergency response** coordination

### Commercial Buildings
- **Automated lighting** based on occupancy and weather
- **Security threat** detection and response
- **Energy cost** reduction and efficiency
- **Compliance reporting** and analytics

### Industrial Facilities
- **Critical infrastructure** protection
- **Weather-resilient** operations
- **Power grid** reliability and backup management
- **Operational efficiency** optimization

## 🔧 Management

### Service Control
```bash

#initially to build the images in the container
docker-compose build

docker-compose up
# Start specific services
docker-compose up cybersecurity-agent weather-agent power-agent

# Scale services
docker-compose up --scale power-agent=2

# View logs
docker-compose logs -f cybersecurity-agent
docker-compose logs -f weather-agent
docker-compose logs -f power-agent

# Stop services
docker-compose down
```

### System Status
```bash
# Check all service health
curl http://localhost:8003/system/status
curl http://localhost:8001/system/status  
curl http://localhost:8002/system/status

# Monitor Kafka topics
open http://localhost:8080  # Kafka UI

# View metrics
open http://localhost:9090  # Prometheus
```

## 📈 Key Benefits

- **🛡️ Enhanced Security**: Automated threat detection and response
- **🌤️ Weather Adaptation**: Intelligent lighting based on conditions
- **⚡ Energy Efficiency**: Optimized power consumption and cost reduction
- **🔄 Unified Management**: Single platform for all lighting operations
- **📊 Complete Visibility**: Real-time monitoring and analytics
- **🚀 Scalable Architecture**: Microservices-based for easy scaling

## 🛠️ Technology Stack

- **AI Framework**: LangChain + LangGraph with Groq LLMs
- **API Framework**: FastAPI with async support
- **Message Broker**: Apache Kafka for real-time communication
- **Databases**: PostgreSQL + Redis for data and caching
- **Monitoring**: Prometheus + Grafana for observability
- **Containerization**: Docker + Docker Compose

## 📚 Documentation

Each service includes comprehensive documentation:

- **[Cybersecurity Service](./backend/cybersecurity/README.md)** - Security agent details
- **[Weather Intelligence Service](./backend/weather/README.md)** - Weather agent details  
- **[Power Grid Management Service](./backend/power/README.md)** - Power agent details

## 🔗 API Integration

All services provide RESTful APIs and can be integrated with existing systems:

- **Building Management Systems** (BMS)
- **SCADA Systems** for industrial control
- **Smart City Platforms**
- **IoT Sensor Networks**
- **Mobile Applications**

---

**Ready to transform your lighting infrastructure with AI-powered intelligence! 🌟🤖**

*For detailed service documentation, API references, and advanced configuration, please refer to the individual service README files.*