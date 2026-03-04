import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class WeatherConfig:
    """Configuration class for weather intelligence agents"""
    
    # API Keys
    WEATHERAPI_API_KEY: str = os.getenv("WEATHERAPI_API_KEY")
    WEATHERAPI_BASE_URL: str = os.getenv("WEATHERAPI_BASE_URL", "https://api.weatherapi.com/v1")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # OpenWeather API Configuration
    OPENWEATHER_BASE_URL: str = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
    OPENWEATHER_FORECAST_URL: str = os.getenv("OPENWEATHER_FORECAST_URL", "https://api.openweathermap.org/data/2.5/forecast")
    OPENWEATHER_UNITS: str = os.getenv("OPENWEATHER_UNITS", "metric")
    
    # Groq LLM Configuration  
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
    
    # Kafka Configuration (Different from cybersecurity)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_WEATHER_ALERTS_TOPIC: str = os.getenv("KAFKA_WEATHER_ALERTS_TOPIC", "weather_alerts")
    KAFKA_WEATHER_DATA_TOPIC: str = os.getenv("KAFKA_WEATHER_DATA_TOPIC", "weather_data")
    KAFKA_WEATHER_FORECASTS_TOPIC: str = os.getenv("KAFKA_WEATHER_FORECASTS_TOPIC", "weather_forecasts")
    KAFKA_WEATHER_REPORTS_TOPIC: str = os.getenv("KAFKA_WEATHER_REPORTS_TOPIC", "weather_reports")
    KAFKA_WEATHER_EMERGENCY_TOPIC: str = os.getenv("KAFKA_WEATHER_EMERGENCY_TOPIC", "weather_emergency")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_WEATHER_CONSUMER_GROUP", "weather_agents")
    KAFKA_TOPIC_COORDINATOR_COMMANDS: str = "coordinator_commands"
    
    # Service Configuration (No conflicts with cybersecurity)
    HOST: str = os.getenv("WEATHER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("WEATHER_PORT", "8001"))
    
    # Monitoring Configuration (Different ports)
    PROMETHEUS_PORT: int = int(os.getenv("WEATHER_PROMETHEUS_PORT", "9091"))
    GRAFANA_PORT: int = int(os.getenv("WEATHER_GRAFANA_PORT", "3002"))
    
    # Weather Data Collection Settings
    FORECAST_HOURS: int = int(os.getenv("FORECAST_HOURS", "48"))
    DATA_COLLECTION_INTERVAL: int = int(os.getenv("DATA_COLLECTION_INTERVAL", "300"))  # 5 minutes
    FORECAST_UPDATE_INTERVAL: int = int(os.getenv("FORECAST_UPDATE_INTERVAL", "3600"))  # 1 hour
    
    # Zone Configuration
    DEFAULT_ZONES: List[str] = [
        "zone_1", "zone_2", "zone_3", "zone_4", "zone_5"
    ]
    ZONE_COORDINATES: Dict[str, Dict[str, float]] = {
        "zone_1": {"lat": 40.7128, "lon": -74.0060},  # NYC example
        "zone_2": {"lat": 40.7589, "lon": -73.9851},
        "zone_3": {"lat": 40.6892, "lon": -74.0445},
        "zone_4": {"lat": 40.7831, "lon": -73.9712},
        "zone_5": {"lat": 40.7282, "lon": -73.7949}
    }
    
    # Weather Thresholds
    VISIBILITY_THRESHOLD: float = float(os.getenv("VISIBILITY_THRESHOLD", "1000"))  # meters
    WIND_SPEED_THRESHOLD: float = float(os.getenv("WIND_SPEED_THRESHOLD", "15"))  # m/s
    PRECIPITATION_THRESHOLD: float = float(os.getenv("PRECIPITATION_THRESHOLD", "5"))  # mm/h
    TEMPERATURE_EXTREME_HIGH: float = float(os.getenv("TEMP_EXTREME_HIGH", "35"))  # Celsius
    TEMPERATURE_EXTREME_LOW: float = float(os.getenv("TEMP_EXTREME_LOW", "-10"))  # Celsius
    
    # Weather Severity Levels
    WEATHER_SEVERITY_LEVELS: Dict[str, int] = {
        "clear": 1,
        "cloudy": 2,
        "light_rain": 3,
        "heavy_rain": 4,
        "storm": 5,
        "severe_storm": 6,
        "fog": 4,
        "snow": 4,
        "extreme_weather": 7
    }

    # Add this line with your other interval settings
    GRAPH_RUN_INTERVAL: int = int(os.getenv("GRAPH_RUN_INTERVAL", "300"))  # 5 minutes
    
    # Emergency Response Thresholds
    EMERGENCY_WIND_SPEED: float = float(os.getenv("EMERGENCY_WIND_SPEED", "25"))  # m/s
    EMERGENCY_PRECIPITATION: float = float(os.getenv("EMERGENCY_PRECIPITATION", "20"))  # mm/h
    FLOOD_RISK_THRESHOLD: float = float(os.getenv("FLOOD_RISK_THRESHOLD", "50"))  # mm/h
    
    # Agent Timeout and Retry Settings
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # Data Quality Settings
    MAX_DATA_AGE: int = int(os.getenv("MAX_DATA_AGE", "1800"))  # 30 minutes
    MIN_CONFIDENCE_SCORE: float = float(os.getenv("MIN_CONFIDENCE_SCORE", "0.7"))
    
    # Lighting Impact Settings
    LOW_LIGHT_THRESHOLD: int = int(os.getenv("LOW_LIGHT_THRESHOLD", "200"))  # lux
    STORM_LIGHTING_BOOST: float = float(os.getenv("STORM_LIGHTING_BOOST", "1.5"))
    FOG_LIGHTING_BOOST: float = float(os.getenv("FOG_LIGHTING_BOOST", "1.3"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate essential configuration"""
        required_keys = [
            cls.WEATHERAPI_API_KEY,
            cls.GROQ_API_KEY
        ]
        
        if not all(required_keys):
            return False
        
        if cls.PORT == 8000:  # Conflict with cybersecurity
            raise ValueError("Weather service port conflicts with cybersecurity service")
        
        if cls.PROMETHEUS_PORT == 9090:  # Conflict with cybersecurity prometheus
            raise ValueError("Weather Prometheus port conflicts with cybersecurity service")
            
        return True
    
    @classmethod
    def get_kafka_config(cls) -> Dict[str, Any]:
        """Get Kafka configuration"""
        return {
            "bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "consumer_group": cls.KAFKA_CONSUMER_GROUP,
            "topics": {
                "weather_alerts": cls.KAFKA_WEATHER_ALERTS_TOPIC,
                "weather_data": cls.KAFKA_WEATHER_DATA_TOPIC,
                "weather_forecasts": cls.KAFKA_WEATHER_FORECASTS_TOPIC,
                "weather_reports": cls.KAFKA_WEATHER_REPORTS_TOPIC,
                "weather_emergency": cls.KAFKA_WEATHER_EMERGENCY_TOPIC
            }
        }
    
    @classmethod
    def get_weatherapi_config(cls) -> Dict[str, Any]:
        """Get WeatherAPI configuration"""
        return {
            "api_key": cls.WEATHERAPI_API_KEY,
            "base_url": cls.WEATHERAPI_BASE_URL
        }
    
    @classmethod
    def get_groq_config(cls) -> Dict[str, Any]:
        """Get Groq LLM configuration"""
        return {
            "api_key": cls.GROQ_API_KEY,
            "model": cls.GROQ_MODEL,
            "temperature": cls.GROQ_TEMPERATURE,
            "max_tokens": cls.GROQ_MAX_TOKENS
        }
    
    @classmethod
    def get_zone_config(cls, zone_id: str) -> Dict[str, Any]:
        """Get configuration for specific zone"""
        if zone_id not in cls.ZONE_COORDINATES:
            raise ValueError(f"Zone {zone_id} not configured")
        
        return {
            "zone_id": zone_id,
            "coordinates": cls.ZONE_COORDINATES[zone_id],
            "thresholds": {
                "visibility": cls.VISIBILITY_THRESHOLD,
                "wind_speed": cls.WIND_SPEED_THRESHOLD,
                "precipitation": cls.PRECIPITATION_THRESHOLD
            }
        }
    
    @classmethod
    def get_emergency_thresholds(cls) -> Dict[str, Any]:
        """Get emergency response thresholds"""
        return {
            "wind_speed": cls.EMERGENCY_WIND_SPEED,
            "precipitation": cls.EMERGENCY_PRECIPITATION,
            "flood_risk": cls.FLOOD_RISK_THRESHOLD
        }

# Create a singleton instance
config = WeatherConfig()

# Validate configuration on import
if not config.validate_config():
    raise RuntimeError("Weather service configuration validation failed")