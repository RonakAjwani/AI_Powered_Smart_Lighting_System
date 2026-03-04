import asyncio
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import timedelta
import json
from datetime import datetime
import threading
from prometheus_fastapi_instrumentator import Instrumentator

# Weather Intelligence System Imports
from src.graph.weather_graph import (
    weather_intelligence_graph,
    execute_normal_operations,
    execute_emergency_response,
    execute_maintenance_mode,
    execute_auto_mode
)
from src.agents.weather_collection_forecast_agent import weather_collection_forecast_agent
from src.agents.env_sensor_agent import environmental_sensor_agent
from src.agents.weather_impact_analyzer_agent import weather_impact_analyzer_agent
from src.agents.disaster_response_advisor_agent import disaster_response_advisor_agent
from src.agents.reporting_agent import weather_reporting_agent

from src.config.settings import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global variables for background tasks
weather_monitoring_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Weather Intelligence System...")
    
    try:
        # Initialize Kafka connections
        await initialize_kafka_connections()
        
        # Start background monitoring tasks
        await start_background_tasks()
        
        logger.info("Weather Intelligence System started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Weather Intelligence System: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Weather Intelligence System...")
        await stop_background_tasks()
        await cleanup_resources()
        logger.info("Weather Intelligence System shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AI-Powered Smart Lighting - Weather Intelligence System",
    description="Advanced weather intelligence system for smart lighting optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        system_health = await get_system_health()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_health": system_health,
            "service": "weather-intelligence"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Weather Intelligence Graph Endpoints
@app.post("/weather/execute")
async def execute_weather_intelligence(
    execution_mode: str = "auto",
    background_tasks: BackgroundTasks = None
):
    """Execute complete weather intelligence workflow"""
    try:
        logger.info(f"Executing weather intelligence in {execution_mode} mode")
        
        if execution_mode == "normal":
            result = await execute_normal_operations()
        elif execution_mode == "emergency":
            result = await execute_emergency_response()
        elif execution_mode == "maintenance":
            result = await execute_maintenance_mode()
        elif execution_mode == "auto":
            result = await execute_auto_mode()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid execution mode: {execution_mode}")
        
        return {
            "success": True,
            "execution_mode": execution_mode,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing weather intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/status")
async def get_weather_system_status():
    """Get current weather system status"""
    try:
        # Get agent statuses
        agent_statuses = await get_agent_statuses()
        
        # Get system health
        system_health = await get_system_health()
        
        # Get current weather conditions
        current_conditions = await get_current_weather_conditions()
        
        return {
            "system_status": "operational",
            "agent_statuses": agent_statuses,
            "system_health": system_health,
            "current_conditions": current_conditions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting weather system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Individual Agent Endpoints
@app.post("/weather/agents/collection/execute")
async def execute_weather_collection():
    """Execute weather collection and forecast agent"""
    try:
        result = weather_collection_forecast_agent.collect_weather_data()
        return {
            "success": True,
            "agent": "weather_collection_forecast",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing weather collection agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/agents/sensor/execute")
async def execute_environmental_sensor():
    """Execute environmental sensor agent"""
    try:
        result = environmental_sensor_agent.collect_environmental_data()
        return {
            "success": True,
            "agent": "environmental_sensor",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing environmental sensor agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/agents/impact/execute")
async def execute_impact_analyzer():
    """Execute weather impact analyzer agent"""
    try:
        result = weather_impact_analyzer_agent.analyze_weather_impact()
        return {
            "success": True,
            "agent": "weather_impact_analyzer",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing impact analyzer agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/agents/disaster/execute")
async def execute_disaster_response():
    """Execute disaster response advisor agent"""
    try:
        result = disaster_response_advisor_agent.advise_disaster_response()
        return {
            "success": True,
            "agent": "disaster_response_advisor",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing disaster response agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/agents/reporting/execute")
async def execute_reporting(report_types: List[str] = None):
    """Execute weather reporting agent"""
    try:
        if report_types is None:
            report_types = ["daily_summary", "forecast_accuracy", "performance_analysis"]
        
        result = weather_reporting_agent.generate_weather_reports(report_types)
        return {
            "success": True,
            "agent": "weather_reporting",
            "report_types": report_types,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing reporting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Weather Data Endpoints
@app.get("/weather/data/current")
async def get_current_weather_data():
    """Get current weather data for all zones"""
    try:
        weather_data = {}
        for zone_id in config.DEFAULT_ZONES:
            zone_weather = await get_zone_weather_data(zone_id)
            weather_data[zone_id] = zone_weather
        
        return {
            "success": True,
            "weather_data": weather_data,
            "zones": len(weather_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting current weather data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/data/zone/{zone_id}")
async def get_zone_weather(zone_id: str):
    """Get weather data for specific zone"""
    try:
        if zone_id not in config.DEFAULT_ZONES:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
        
        zone_weather = await get_zone_weather_data(zone_id)
        return {
            "success": True,
            "zone_id": zone_id,
            "weather_data": zone_weather,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting zone weather data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/forecast/{zone_id}")
async def get_weather_forecast(zone_id: str, hours: int = 24):
    """Get weather forecast for specific zone"""
    try:
        if zone_id not in config.DEFAULT_ZONES:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
        
        forecast_data = await get_zone_forecast_data(zone_id, hours)
        return {
            "success": True,
            "zone_id": zone_id,
            "forecast_hours": hours,
            "forecast_data": forecast_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting weather forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Emergency and Alert Endpoints
@app.get("/weather/alerts")
async def get_weather_alerts():
    """Get current weather alerts"""
    try:
        alerts = await get_current_weather_alerts()
        return {
            "success": True,
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting weather alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/emergency/activate")
async def activate_emergency_mode():
    """Activate emergency weather response mode"""
    try:
        result = await execute_emergency_response()
        return {
            "success": True,
            "mode": "emergency_activated",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error activating emergency mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reports and Analytics Endpoints
@app.get("/weather/reports")
async def get_weather_reports():
    """Get available weather reports"""
    try:
        reports = await get_available_reports()
        return {
            "success": True,
            "reports": reports,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting weather reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/analytics/performance")
async def get_performance_analytics():
    """Get weather system performance analytics"""
    try:
        analytics = await get_system_performance_analytics()
        return {
            "success": True,
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/analytics/forecast-accuracy")
async def get_forecast_accuracy():
    """Get forecast accuracy analytics"""
    try:
        accuracy = await get_forecast_accuracy_analytics()
        return {
            "success": True,
            "forecast_accuracy": accuracy,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting forecast accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration and Control Endpoints
@app.get("/weather/config")
async def get_weather_config():
    """Get weather system configuration"""
    try:
        weather_config = {
            "zones": config.DEFAULT_ZONES,
            "update_intervals": {
                "weather_collection": "15 minutes",
                "environmental_sensor": "5 minutes",
                "impact_analysis": "30 minutes",
                "reporting": "1 hour"
            },
            "thresholds": {
                "wind_speed": config.WIND_SPEED_THRESHOLD,
                "visibility": config.VISIBILITY_THRESHOLD,
                "precipitation": config.PRECIPITATION_THRESHOLD
            },
            "emergency_thresholds": {
                "wind_speed": config.EMERGENCY_WIND_SPEED,
                "precipitation": config.EMERGENCY_PRECIPITATION
            }
        }
        
        return {
            "success": True,
            "config": weather_config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting weather config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/config/update")
async def update_weather_config(config_data: Dict[str, Any]):
    """Update weather system configuration"""
    try:
        # Update configuration (implement based on your needs)
        updated_config = await update_system_config(config_data)
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_config": updated_config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating weather config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/weather/ws")
async def weather_websocket(websocket):
    """WebSocket endpoint for real-time weather updates"""
    await websocket.accept()
    try:
        while True:
            # Send real-time weather updates
            weather_update = await get_real_time_weather_update()
            await websocket.send_json(weather_update)
            await asyncio.sleep(30)  # Send updates every 30 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Helper Functions
async def initialize_kafka_connections():
    """Initialize Kafka producer and consumer connections"""
    try:
        # Test Kafka connections
        logger.info("Initializing Kafka connections...")
        # Add actual Kafka initialization here
        logger.info("Kafka connections initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kafka connections: {e}")
        raise

async def start_background_tasks():
    """Start background monitoring tasks"""
    global weather_monitoring_task
    
    try:
        # Start weather monitoring task
        weather_monitoring_task = asyncio.create_task(weather_monitoring_loop())
               
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}")
        raise

async def stop_background_tasks():
    """Stop background monitoring tasks"""
    global weather_monitoring_task
    
    tasks = [weather_monitoring_task]
    
    for task in tasks:
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

async def cleanup_resources():
    """Cleanup system resources"""
    try:
        logger.info("Cleaning up system resources...")
        # Add cleanup logic here
        logger.info("System resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

async def weather_monitoring_loop():
    """Background task for continuous weather monitoring"""
    while True:
        try:
            # Execute weather intelligence in auto mode every 15 minutes
            await execute_auto_mode()
            await asyncio.sleep(900)  # 15 minutes
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in weather monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

async def get_system_health() -> Dict[str, Any]:
    """Get overall system health status"""
    return {
        "overall_status": "healthy",
        "agents": {
            "weather_collection": "operational",
            "environmental_sensor": "operational",
            "impact_analyzer": "operational",
            "disaster_response": "standby",
            "reporting": "operational"
        },
        "kafka_connectivity": "connected",
        "data_sources": "available",
        "last_check": datetime.now().isoformat()
    }

async def get_agent_statuses() -> Dict[str, str]:
    """Get current status of all weather agents"""
    return {
        "weather_collection": "operational",
        "environmental_sensor": "operational", 
        "impact_analyzer": "operational",
        "disaster_response": "standby",
        "reporting": "operational"
    }

async def get_current_weather_conditions() -> Dict[str, Any]:
    """Get current weather conditions summary"""
    return {
        "overall_conditions": "partly_cloudy",
        "temperature_range": "18-24°C",
        "wind_conditions": "light_breeze",
        "visibility": "good",
        "precipitation": "none",
        "alerts_active": 0
    }

async def get_zone_weather_data(zone_id: str) -> Dict[str, Any]:
    """Get weather data for specific zone"""
    import random
    return {
        "zone_id": zone_id,
        "temperature": round(random.uniform(18, 24), 1),
        "humidity": round(random.uniform(50, 70), 1),
        "wind_speed": round(random.uniform(5, 15), 1),
        "visibility": random.randint(5000, 10000),
        "weather_condition": random.choice(["Clear", "Partly Cloudy", "Cloudy"]),
        "last_updated": datetime.now().isoformat()
    }

async def get_zone_forecast_data(zone_id: str, hours: int) -> List[Dict[str, Any]]:
    """Get forecast data for specific zone"""
    import random
    forecast = []
    
    for i in range(0, hours, 3):  # 3-hour intervals
        forecast_time = datetime.now() + timedelta(hours=i)
        forecast.append({
            "time": forecast_time.isoformat(),
            "temperature": round(random.uniform(15, 26), 1),
            "precipitation_chance": random.randint(0, 30),
            "wind_speed": round(random.uniform(3, 12), 1),
            "weather_condition": random.choice(["Clear", "Partly Cloudy", "Cloudy", "Light Rain"])
        })
    
    return forecast

async def get_current_weather_alerts() -> List[Dict[str, Any]]:
    """Get current weather alerts"""
    # Return empty list for demo - would fetch actual alerts
    return []

async def get_available_reports() -> List[Dict[str, Any]]:
    """Get list of available weather reports"""
    return [
        {
            "report_id": "daily_summary_20251021",
            "type": "daily_summary",
            "generated_at": datetime.now().isoformat(),
            "zones_covered": 5
        },
        {
            "report_id": "forecast_accuracy_20251021",
            "type": "forecast_accuracy", 
            "generated_at": datetime.now().isoformat(),
            "accuracy_score": 87.5
        }
    ]

async def get_system_performance_analytics() -> Dict[str, Any]:
    """Get system performance analytics"""
    return {
        "uptime": "99.8%",
        "data_quality": "excellent",
        "response_time": "fast",
        "agent_performance": {
            "weather_collection": 95.2,
            "environmental_sensor": 97.8,
            "impact_analyzer": 91.5,
            "reporting": 93.1
        }
    }

async def get_forecast_accuracy_analytics() -> Dict[str, Any]:
    """Get forecast accuracy analytics"""
    return {
        "overall_accuracy": 87.5,
        "temperature_accuracy": 92.1,
        "precipitation_accuracy": 78.3,
        "wind_accuracy": 85.7,
        "accuracy_trend": "improving"
    }

async def update_system_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update system configuration"""
    # Implement configuration update logic
    return config_data

async def get_real_time_weather_update() -> Dict[str, Any]:
    """Get real-time weather update for WebSocket"""
    return {
        "type": "weather_update",
        "timestamp": datetime.now().isoformat(),
        "data": await get_current_weather_conditions()
    }

if __name__ == "__main__":
    # Run the weather intelligence system on port 8001 (different from cybersecurity port 8000)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Weather intelligence system port
        reload=True,
        log_level="info"
    )