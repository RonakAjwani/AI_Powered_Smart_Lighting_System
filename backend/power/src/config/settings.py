import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PowerGridConfig:
    """Configuration class for power grid management agents"""
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Groq Configuration
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
    
    # Service Configuration
    POWER_HOST: str = os.getenv("POWER_HOST", "0.0.0.0")
    POWER_PORT: int = int(os.getenv("POWER_PORT", "8002"))
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_POWER_CONSUMER_GROUP: str = os.getenv("KAFKA_POWER_CONSUMER_GROUP", "power_agents")
    
    # Kafka Topics
    KAFKA_ENERGY_LOAD_TOPIC: str = os.getenv("KAFKA_ENERGY_LOAD_TOPIC", "energy_load_data")
    KAFKA_POWER_OUTAGE_TOPIC: str = os.getenv("KAFKA_POWER_OUTAGE_TOPIC", "power_outages")
    KAFKA_ENERGY_REROUTING_TOPIC: str = os.getenv("KAFKA_ENERGY_REROUTING_TOPIC", "energy_rerouting")
    KAFKA_POWER_REPORTS_TOPIC: str = os.getenv("KAFKA_POWER_REPORTS_TOPIC", "power_reports")
    KAFKA_GRID_ALERTS_TOPIC: str = os.getenv("KAFKA_GRID_ALERTS_TOPIC", "grid_alerts")
    KAFKA_TOPIC_COORDINATOR_COMMANDS: str = "coordinator_commands"
    
    # Zone Configuration
    DEFAULT_ZONES: List[str] = [
        "zone_1", "zone_2", "zone_3", "zone_4", "zone_5",
        "zone_6", "zone_7", "zone_8", "zone_9", "zone_10"
    ]
    
    # Energy Thresholds
    PEAK_DEMAND_THRESHOLD: float = float(os.getenv("PEAK_DEMAND_THRESHOLD", "85.0"))  # %
    LOW_VOLTAGE_THRESHOLD: float = float(os.getenv("LOW_VOLTAGE_THRESHOLD", "0.95"))  # per unit
    HIGH_VOLTAGE_THRESHOLD: float = float(os.getenv("HIGH_VOLTAGE_THRESHOLD", "1.05"))  # per unit
    OUTAGE_DETECTION_THRESHOLD: float = float(os.getenv("OUTAGE_DETECTION_THRESHOLD", "0.8"))  # per unit
    
    # Power Quality Thresholds
    FREQUENCY_MIN: float = float(os.getenv("FREQUENCY_MIN", "49.5"))  # Hz
    FREQUENCY_MAX: float = float(os.getenv("FREQUENCY_MAX", "50.5"))  # Hz
    POWER_FACTOR_MIN: float = float(os.getenv("POWER_FACTOR_MIN", "0.85"))
    
    # Load Forecasting Parameters
    FORECAST_HORIZON_HOURS: int = int(os.getenv("FORECAST_HORIZON_HOURS", "24"))
    HISTORICAL_DATA_DAYS: int = int(os.getenv("HISTORICAL_DATA_DAYS", "30"))
    FORECAST_UPDATE_INTERVAL: int = int(os.getenv("FORECAST_UPDATE_INTERVAL", "900"))  # 15 minutes
    
    # Energy Optimization Parameters
    MIN_DIMMING_LEVEL: float = float(os.getenv("MIN_DIMMING_LEVEL", "20.0"))  # %
    MAX_BRIGHTNESS_LEVEL: float = float(os.getenv("MAX_BRIGHTNESS_LEVEL", "100.0"))  # %
    ENERGY_SAVINGS_TARGET: float = float(os.getenv("ENERGY_SAVINGS_TARGET", "15.0"))  # %
    
    # Priority Zones (Critical Infrastructure)
    PRIORITY_ZONES: List[str] = [
        "hospital_zone", "emergency_services", "traffic_control",
        "communication_hub", "water_treatment", "airport_zone"
    ]
    
    # Emergency Response Parameters
    OUTAGE_RESPONSE_TIME: int = int(os.getenv("OUTAGE_RESPONSE_TIME", "5"))  # seconds
    REROUTING_TIMEOUT: int = int(os.getenv("REROUTING_TIMEOUT", "30"))  # seconds
    EMERGENCY_BACKUP_CAPACITY: float = float(os.getenv("EMERGENCY_BACKUP_CAPACITY", "40.0"))  # %
    
    # Agent Execution Settings
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "60"))  # seconds
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    
    # Data Collection Intervals (seconds)
    LOAD_MONITORING_INTERVAL: int = int(os.getenv("LOAD_MONITORING_INTERVAL", "60"))
    OUTAGE_DETECTION_INTERVAL: int = int(os.getenv("OUTAGE_DETECTION_INTERVAL", "5"))
    OPTIMIZATION_INTERVAL: int = int(os.getenv("OPTIMIZATION_INTERVAL", "300"))  # 5 minutes
    REPORTING_INTERVAL: int = int(os.getenv("REPORTING_INTERVAL", "3600"))  # 1 hour
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://power_user:power_pass@localhost:5432/power_grid_db")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "power_grid.log")
    
    def get_groq_config(self) -> Dict[str, Any]:
        """Get Groq LLM configuration"""
        return {
            "api_key": self.GROQ_API_KEY,
            "model": self.GROQ_MODEL,
            "temperature": self.GROQ_TEMPERATURE,
            "max_tokens": self.GROQ_MAX_TOKENS
        }
    
    def get_kafka_config(self) -> Dict[str, Any]:
        """Get Kafka configuration"""
        return {
            "bootstrap_servers": self.KAFKA_BOOTSTRAP_SERVERS,
            "consumer_group": self.KAFKA_POWER_CONSUMER_GROUP,
            "topics": {
                "energy_load": self.KAFKA_ENERGY_LOAD_TOPIC,
                "power_outage": self.KAFKA_POWER_OUTAGE_TOPIC,
                "energy_rerouting": self.KAFKA_ENERGY_REROUTING_TOPIC,
                "power_reports": self.KAFKA_POWER_REPORTS_TOPIC,
                "grid_alerts": self.KAFKA_GRID_ALERTS_TOPIC
            }
        }
    
    def get_zone_config(self) -> Dict[str, Any]:
        """Get zone configuration"""
        return {
            "default_zones": self.DEFAULT_ZONES,
            "priority_zones": self.PRIORITY_ZONES,
            "total_zones": len(self.DEFAULT_ZONES)
        }
    
    def get_threshold_config(self) -> Dict[str, Any]:
        """Get threshold configuration"""
        return {
            "peak_demand": self.PEAK_DEMAND_THRESHOLD,
            "voltage_limits": {
                "low": self.LOW_VOLTAGE_THRESHOLD,
                "high": self.HIGH_VOLTAGE_THRESHOLD,
                "outage": self.OUTAGE_DETECTION_THRESHOLD
            },
            "frequency_limits": {
                "min": self.FREQUENCY_MIN,
                "max": self.FREQUENCY_MAX
            },
            "power_factor_min": self.POWER_FACTOR_MIN
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        if not self.GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set")
            return False
        
        if self.POWER_PORT < 1024 or self.POWER_PORT > 65535:
            print("WARNING: Invalid POWER_PORT range")
            return False
        
        if self.FORECAST_HORIZON_HOURS < 1 or self.FORECAST_HORIZON_HOURS > 168:
            print("WARNING: Invalid FORECAST_HORIZON_HOURS (should be 1-168)")
            return False
        
        return True

# Create a singleton instance
config = PowerGridConfig()

# Validate configuration on import
if not config.validate_config():
    print("Configuration validation failed - check your settings")