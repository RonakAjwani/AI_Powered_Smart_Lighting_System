import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Find the .env file path
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if not os.path.exists(dotenv_path):
    # Fallback for container environment
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env.example')
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"

    # --- THIS IS THE FIX ---
    # Changed default from kafka:9092 to kafka:29092
    # This now matches the internal advertised listener
    KAFKA_BROKER_URL: str = "kafka:29092" 
    # ----------------------

    KAFKA_CLIENT_ID: str = "coordinator-agent"
    KAFKA_GROUP_ID: str = "coordinator-group"

    # Input Topics
    KAFKA_TOPIC_CYBER_ALERTS: str = "cyber_alerts"
    KAFKA_TOPIC_CYBER_REPORTS: str = "incident_reports"
    KAFKA_TOPIC_WEATHER_ALERTS: str = "weather_alerts"
    KAFKA_TOPIC_WEATHER_IMPACT: str = "weather_impact_analysis"
    KAFKA_TOPIC_POWER_ALERTS: str = "power_outages"
    KAFKA_TOPIC_POWER_FORECASTS: str = "load_forecast_data"
    KAFKA_TOPIC_POWER_OPTIMIZATION: str = "optimization_results"

    # Output Topics
    KAFKA_TOPIC_COORDINATOR_COMMANDS: str = "coordinator_commands"
    KAFKA_SYSTEM_LOGS_TOPIC: str = "system_logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()