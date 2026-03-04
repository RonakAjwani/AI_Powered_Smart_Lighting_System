import json
import logging
import threading
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from ..config.settings import config
import src.graph.weather_graph as weather_graph

logger = logging.getLogger(__name__)

class WeatherKafkaConsumer:
    """
    Kafka consumer for weather intelligence data processing.
    Listens to weather events and triggers appropriate agent responses.
    """
    
    def __init__(self):
        self.kafka_config = config.get_kafka_config()
        self.consumer = None
        self.is_running = False
        self.consumer_thread = None
        
        # Topics to monitor
        self.topics = [
            'weather_alerts',
            'weather_data', 
            'weather_forecasts',
            'weather_emergency',
            'lighting_commands',
            'coordinator_commands'  # Listen to lighting system responses
        ]
        
        # Message handlers for different event types
        self.handlers = {
            'weather_forecast': self._handle_weather_forecast,
            'sensor_data': self._handle_sensor_data,
            'weather_alert': self._handle_weather_alert,
            'emergency_protocol': self._handle_emergency_protocol,
            'impact_analysis': self._handle_impact_analysis,
            'lighting_command': self._handle_lighting_command,
            'forecast_deviation': self._handle_forecast_deviation
        }
    
    def _create_consumer(self):
        """Create Kafka consumer instance"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                group_id=self.kafka_config.get('consumer_group', 'weather_agents'),
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
                max_poll_records=50
            )
            logger.info(f"Weather Kafka consumer created for topics: {self.topics}")
            
        except Exception as e:
            logger.error(f"Failed to create Weather Kafka consumer: {e}")
            raise
    
    def start_consuming(self):
        """Start consuming messages in a separate thread"""
        if self.is_running:
            logger.warning("Weather consumer is already running")
            return
        
        try:
            self._create_consumer()
            self.is_running = True
            
            # Start consumer thread
            self.consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
            self.consumer_thread.start()
            
            logger.info("Weather Kafka consumer started")
            
        except Exception as e:
            logger.error(f"Failed to start weather consumer: {e}")
            self.is_running = False
            raise
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Weather Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing weather consumer: {e}")
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
            logger.info("Weather consumer thread stopped")
    
    def _consume_messages(self):
        """Main message consumption loop"""
        logger.info("Starting weather message consumption loop")
        
        while self.is_running:
            try:
                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)
                
                if not message_batch:
                    continue
                
                # Process messages from all topics
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            self._process_message(message)
                        except Exception as e:
                            logger.error(f"Error processing weather message: {e}")
                            continue
                
            except KafkaError as e:
                logger.error(f"Kafka error during weather consumption: {e}")
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Unexpected error in weather consumption loop: {e}")
                time.sleep(1)
        
        logger.info("Weather message consumption loop ended")

    def _handle_coordinator_command(self, command: Dict[str, Any]):
        logger.info(f"Received coordinator command: {command}")
        target = command.get("target_service")
        payload = command.get("payload", {})
        mode = payload.get("mode")

        # Check if this command is for this service
        if target != "all" and target != "weather":
            logger.info(f"Coordinator command not targeted at 'weather' service. Ignoring.")
            return

        logger.warn(f"EXECUTING COORDINATOR COMMAND: Set mode to {mode}")
        logger.warn(f"Reason: {payload.get('reason')}")
        logger.warn(f"Full Payload: {payload}")
        # Log this event using your existing log function
        self._log_event("coordinator_command", command)
    
    def _process_message(self, message):
        """Process individual Kafka message"""
        try:
            # Extract message data
            topic = message.topic
            key = message.key
            value = message.value
            timestamp = datetime.fromtimestamp(message.timestamp / 1000)
            
            logger.debug(f"Processing weather message from topic {topic}: {key}")
            
            if topic == config.KAFKA_TOPIC_COORDINATOR_COMMANDS:
                self._handle_coordinator_command(value)
                return
            
            if not isinstance(value, dict):
                logger.warning(f"Invalid weather message format from {topic}: {type(value)}")
                return
            
            # Get event type
            event_type = value.get('event_type', 'unknown')
            
            # Add metadata
            value['kafka_metadata'] = {
                'topic': topic,
                'key': key,
                'timestamp': timestamp.isoformat(),
                'partition': message.partition,
                'offset': message.offset
            }
            
            # Route to appropriate handler
            handler = self.handlers.get(event_type, self._handle_generic_event)
            handler(value)
            
        except Exception as e:
            logger.error(f"Error processing weather message: {e}")
    
    def _handle_weather_forecast(self, data: Dict[str, Any]):
        """Handle weather forecast events"""
        zone_id = data.get('zone_id', 'unknown')
        confidence = data.get('confidence_score', 0.0)
        
        logger.info(f"Weather forecast received for {zone_id} (confidence: {confidence})")
        
        # Trigger impact analysis if confidence is high
        if confidence >= config.MIN_CONFIDENCE_SCORE:
            try:
                result = weather_graph.execute_targeted_analysis("impact")
                logger.info(f"Impact analysis triggered for forecast: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in forecast impact analysis: {e}")
        
        self._log_event("weather_forecast", data)
    
    def _handle_sensor_data(self, data: Dict[str, Any]):
        """Handle environmental sensor data events"""
        zone_id = data.get('zone_id', 'unknown')
        readings = data.get('sensor_readings', {})
        
        logger.debug(f"Sensor data received from zone: {zone_id}")
        
        # Check for extreme conditions
        if self._has_extreme_conditions(readings):
            logger.warning(f"Extreme weather conditions detected in {zone_id}")
            
            try:
                # Trigger emergency analysis
                result = weather_graph.execute_targeted_analysis("emergency")
                logger.info(f"Emergency analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in emergency analysis: {e}")
        
        # Check for forecast deviation
        if self._has_forecast_deviation(readings, zone_id):
            logger.info(f"Forecast deviation detected in {zone_id}")
            
            try:
                # Trigger forecast update
                result = weather_graph.execute_targeted_analysis("forecast")
                logger.info(f"Forecast update triggered: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in forecast update: {e}")
        
        self._log_event("sensor_data", data)
    
    def _handle_weather_alert(self, data: Dict[str, Any]):
        """Handle weather alert events"""
        zone_id = data.get('zone_id', 'unknown')
        alert_type = data.get('alert_type', 'unknown')
        severity = data.get('severity', 'low')
        
        logger.info(f"Weather alert: {alert_type} ({severity}) for {zone_id}")
        
        # Trigger lighting impact analysis for high severity alerts
        if severity in ['high', 'critical']:
            try:
                result = weather_graph.execute_targeted_analysis("impact")
                logger.info(f"High severity alert impact analysis: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in alert impact analysis: {e}")
        
        self._log_event("weather_alert", data)
    
    def _handle_emergency_protocol(self, data: Dict[str, Any]):
        """Handle emergency weather protocol events"""
        emergency_type = data.get('emergency_type', 'unknown')
        affected_zones = data.get('affected_zones', [])
        
        logger.warning(f"Emergency protocol: {emergency_type} affecting {len(affected_zones)} zones")
        
        try:
            # Always trigger full analysis for emergencies
            result = weather_graph.execute_weather_analysis()
            logger.warning(f"Emergency weather analysis: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Error in emergency weather analysis: {e}")
        
        self._log_event("emergency_protocol", data)
    
    def _handle_impact_analysis(self, data: Dict[str, Any]):
        """Handle impact analysis events"""
        zone_id = data.get('zone_id', 'unknown')
        severity_matrix = data.get('severity_matrix', {})
        
        logger.info(f"Impact analysis for {zone_id}: severity {severity_matrix.get('severity_score', 'unknown')}")
        
        self._log_event("impact_analysis", data)
    
    def _handle_lighting_command(self, data: Dict[str, Any]):
        """Handle lighting system command responses"""
        command_type = data.get('command_type', 'unknown')
        success = data.get('success', False)
        
        logger.info(f"Lighting command response: {command_type} ({'success' if success else 'failed'})")
        
        self._log_event("lighting_command", data)
    
    def _handle_forecast_deviation(self, data: Dict[str, Any]):
        """Handle forecast deviation events"""
        zone_id = data.get('zone_id', 'unknown')
        deviation_type = data.get('deviation_type', 'unknown')
        
        logger.info(f"Forecast deviation: {deviation_type} in {zone_id}")
        
        try:
            # Trigger forecast accuracy analysis
            result = weather_graph.execute_targeted_analysis("forecast")
            logger.info(f"Forecast accuracy analysis: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Error in forecast accuracy analysis: {e}")
        
        self._log_event("forecast_deviation", data)
    
    def _handle_generic_event(self, data: Dict[str, Any]):
        """Handle generic/unknown events"""
        event_type = data.get('event_type', 'unknown')
        logger.debug(f"Generic weather event received: {event_type}")
        
        self._log_event("generic", data)
    
    def _has_extreme_conditions(self, readings: Dict[str, Any]) -> bool:
        """Check if sensor readings indicate extreme conditions"""
        try:
            wind_speed = readings.get('wind_speed', 0)
            precipitation = readings.get('precipitation', 0)
            temperature = readings.get('temperature', 20)
            visibility = readings.get('visibility', 10000)
            
            return (
                wind_speed > config.EMERGENCY_WIND_SPEED or
                precipitation > config.EMERGENCY_PRECIPITATION or
                temperature > config.TEMPERATURE_EXTREME_HIGH or
                temperature < config.TEMPERATURE_EXTREME_LOW or
                visibility < config.VISIBILITY_THRESHOLD / 2
            )
        except Exception as e:
            logger.error(f"Error checking extreme conditions: {e}")
            return False
    
    def _has_forecast_deviation(self, readings: Dict[str, Any], zone_id: str) -> bool:
        """Check if readings deviate significantly from forecast"""
        try:
            # This would compare with stored forecast data
            # For now, simple threshold-based check
            temperature = readings.get('temperature', 20)
            precipitation = readings.get('precipitation', 0)
            
            # Simplified deviation check (would be enhanced with forecast comparison)
            return (
                abs(temperature - 20) > 10 or  # 10 degree deviation
                precipitation > config.PRECIPITATION_THRESHOLD * 2  # Double expected rain
            )
        except Exception as e:
            logger.error(f"Error checking forecast deviation: {e}")
            return False
    
    def _log_event(self, event_category: str, data: Dict[str, Any]):
        """Log event for monitoring and debugging"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "category": event_category,
                "event_type": data.get('event_type', 'unknown'),
                "zone_id": data.get('zone_id', 'unknown'),
                "severity": data.get('severity', 'unknown')
            }
            
            logger.debug(f"Weather event logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging weather event: {e}")
    
    def get_consumer_status(self) -> Dict[str, Any]:
        """Get current consumer status"""
        return {
            "is_running": self.is_running,
            "topics": self.topics,
            "thread_alive": self.consumer_thread.is_alive() if self.consumer_thread else False,
            "consumer_active": self.consumer is not None,
            "timestamp": datetime.now().isoformat()
        }

# Create consumer instance
weather_consumer = WeatherKafkaConsumer()