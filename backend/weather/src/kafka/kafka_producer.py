import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from ..config.settings import config

logger = logging.getLogger(__name__)

class WeatherKafkaProducer:
    """
    Kafka producer for weather intelligence data publishing.
    Publishes weather forecasts, sensor data, alerts, and reports.
    """
    
    def __init__(self):
        self.kafka_config = config.get_kafka_config()
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
                compression_type='gzip'
            )
            logger.info("Weather Kafka producer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weather Kafka producer: {e}")
            raise
    
    def publish_weather_forecast(self, zone_id: str, forecast_data: Dict[str, Any], 
                               confidence_score: float = 0.8) -> bool:
        """Publish weather forecast for a zone"""
        try:
            message = {
                "event_type": "weather_forecast",
                "forecast_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id,
                "confidence_score": confidence_score,
                "forecast_data": forecast_data,
                "source": "weather_collection_forecast_agent"
            }
            
            key = f"forecast_{zone_id}_{message['forecast_id']}"
            
            future = self.producer.send('weather_forecasts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Weather forecast published for {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish weather forecast: {e}")
            return False
    
    def publish_sensor_data(self, zone_id: str, sensor_readings: Dict[str, Any]) -> bool:
        """Publish environmental sensor data"""
        try:
            message = {
                "event_type": "sensor_data",
                "data_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id,
                "sensor_readings": sensor_readings,
                "data_quality": "good",  # Can be enhanced with quality checks
                "source": "environmental_sensor_agent"
            }
            
            key = f"sensor_{zone_id}_{message['data_id']}"
            
            future = self.producer.send('weather_data', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Sensor data published for {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish sensor data: {e}")
            return False
    
    def publish_weather_alert(self, zone_id: str, alert_type: str, severity: str, 
                            details: Dict[str, Any] = None) -> bool:
        """Publish weather alert for lighting adjustments"""
        try:
            message = {
                "event_type": "weather_alert",
                "alert_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id,
                "alert_type": alert_type,  # fog, storm, low_visibility, etc.
                "severity": severity,  # low, medium, high, critical
                "lighting_impact": True,
                "details": details or {},
                "source": "weather_impact_analyzer"
            }
            
            key = f"alert_{zone_id}_{message['alert_id']}"
            
            future = self.producer.send('weather_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Weather alert published: {alert_type} ({severity}) for {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish weather alert: {e}")
            return False
    
    def publish_emergency_protocol(self, emergency_type: str, affected_zones: List[str], 
                                 protocol_data: Dict[str, Any]) -> bool:
        """Publish emergency weather protocol"""
        try:
            message = {
                "event_type": "emergency_protocol",
                "emergency_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "emergency_type": emergency_type,  # storm, flood, extreme_weather
                "affected_zones": affected_zones,
                "priority": "critical",
                "protocol_data": protocol_data,
                "source": "disaster_response_advisor"
            }
            
            key = f"emergency_{emergency_type}_{message['emergency_id']}"
            
            future = self.producer.send('weather_emergency', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.warning(f"Emergency protocol published: {emergency_type} affecting {len(affected_zones)} zones")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish emergency protocol: {e}")
            return False
    
    def publish_weather_report(self, report_type: str, report_data: Dict[str, Any]) -> bool:
        """Publish weather intelligence report"""
        try:
            message = {
                "event_type": "weather_report",
                "report_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "report_type": report_type,  # daily_summary, forecast_accuracy, impact_analysis
                "report_data": report_data,
                "source": "weather_reporting_agent"
            }
            
            key = f"report_{report_type}_{message['report_id']}"
            
            future = self.producer.send('weather_reports', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Weather report published: {report_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish weather report: {e}")
            return False
    
    def publish_impact_analysis(self, zone_id: str, current_conditions: Dict[str, Any], 
                              lighting_recommendations: Dict[str, Any]) -> bool:
        """Publish weather impact analysis for lighting"""
        try:
            message = {
                "event_type": "impact_analysis",
                "analysis_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "zone_id": zone_id,
                "current_conditions": current_conditions,
                "lighting_recommendations": lighting_recommendations,
                "severity_matrix": self._calculate_severity_matrix(current_conditions),
                "source": "weather_impact_analyzer"
            }
            
            key = f"impact_{zone_id}_{message['analysis_id']}"
            
            future = self.producer.send('weather_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Impact analysis published for {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish impact analysis: {e}")
            return False
    
    def publish_batch_weather_data(self, batch_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Publish multiple weather events in batch"""
        results = {"success": 0, "failed": 0}
        
        for data in batch_data:
            try:
                event_type = data.get("event_type", "unknown")
                
                if event_type == "weather_forecast":
                    success = self.publish_weather_forecast(
                        data.get("zone_id", "unknown"),
                        data.get("forecast_data", {}),
                        data.get("confidence_score", 0.8)
                    )
                elif event_type == "sensor_data":
                    success = self.publish_sensor_data(
                        data.get("zone_id", "unknown"),
                        data.get("sensor_readings", {})
                    )
                elif event_type == "weather_alert":
                    success = self.publish_weather_alert(
                        data.get("zone_id", "unknown"),
                        data.get("alert_type", "unknown"),
                        data.get("severity", "low"),
                        data.get("details", {})
                    )
                else:
                    logger.warning(f"Unknown event type for batch publish: {event_type}")
                    success = False
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error in batch weather data publish: {e}")
                results["failed"] += 1
        
        logger.info(f"Batch weather publish: {results['success']} success, {results['failed']} failed")
        return results
    
    def _calculate_severity_matrix(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate severity matrix for weather conditions"""
        severity_score = 1  # Base score
        
        # Wind impact
        wind_speed = conditions.get("wind_speed", 0)
        if wind_speed > config.EMERGENCY_WIND_SPEED:
            severity_score += 3
        elif wind_speed > config.WIND_SPEED_THRESHOLD:
            severity_score += 2
        
        # Precipitation impact
        precipitation = conditions.get("precipitation", 0)
        if precipitation > config.EMERGENCY_PRECIPITATION:
            severity_score += 3
        elif precipitation > config.PRECIPITATION_THRESHOLD:
            severity_score += 2
        
        # Visibility impact
        visibility = conditions.get("visibility", 10000)
        if visibility < config.VISIBILITY_THRESHOLD / 2:
            severity_score += 2
        elif visibility < config.VISIBILITY_THRESHOLD:
            severity_score += 1
        
        return {
            "severity_score": min(severity_score, 7),  # Cap at 7
            "lighting_adjustment": min(severity_score * 0.2, 1.5),  # Max 150% boost
            "priority": "critical" if severity_score >= 6 else "high" if severity_score >= 4 else "normal"
        }
    
    def flush(self):
        """Flush all pending messages"""
        try:
            self.producer.flush(timeout=30)
            logger.info("Weather producer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing weather producer: {e}")
    
    def close(self):
        """Close the producer"""
        try:
            if self.producer:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
                logger.info("Weather Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing weather producer: {e}")
    
    def get_producer_status(self) -> Dict[str, Any]:
        """Get current producer status"""
        return {
            "producer_active": self.producer is not None,
            "topics": list(self.kafka_config['topics'].values()),
            "config": {
                "bootstrap_servers": self.kafka_config['bootstrap_servers'],
                "compression": "gzip",
                "acks": "all"
            },
            "timestamp": datetime.now().isoformat()
        }

# Create producer instance
weather_producer = WeatherKafkaProducer()