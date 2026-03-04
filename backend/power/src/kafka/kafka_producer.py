import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import asyncio
from datetime import datetime

from ..config.settings import config

# Configure logging
logger = logging.getLogger(__name__)

class PowerGridKafkaProducer:
    """Kafka producer for power grid management data"""
    
    def __init__(self):
        self.producer = None
        self.kafka_config = config.get_kafka_config()
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer with configuration"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
                compression_type=None,
            )
            logger.info("Power Grid Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def send_energy_load_data(self, zone_id: str, load_data: Dict[str, Any]) -> bool:
        """Send energy load data to Kafka topic"""
        try:
            topic = self.kafka_config["topics"]["energy_load"]
            message = {
                "zone_id": zone_id,
                "timestamp": datetime.now().isoformat(),
                "load_data": load_data,
                "message_type": "energy_load"
            }
            
            future = self.producer.send(topic, key=zone_id, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Energy load data sent to {topic} - Partition: {record_metadata.partition}, Offset: {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send energy load data: {e}")
            return False
    
    def send_power_outage_alert(self, outage_data: Dict[str, Any]) -> bool:
        """Send power outage alert to Kafka topic"""
        try:
            topic = self.kafka_config["topics"]["power_outage"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "outage_data": outage_data,
                "message_type": "power_outage",
                "severity": outage_data.get("severity", "medium")
            }
            
            # Use affected zone as key for partitioning
            key = outage_data.get("affected_zones", ["unknown"])[0]
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.warning(f"Power outage alert sent to {topic} - Severity: {message['severity']}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send power outage alert: {e}")
            return False
    
    def send_rerouting_command(self, rerouting_data: Dict[str, Any]) -> bool:
        """Send energy rerouting command to Kafka topic"""
        try:
            topic = self.kafka_config["topics"]["energy_rerouting"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "rerouting_data": rerouting_data,
                "message_type": "energy_rerouting",
                "priority": rerouting_data.get("priority", "medium")
            }
            
            # Use command_id as key
            key = rerouting_data.get("command_id", "default")
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Rerouting command sent to {topic} - Priority: {message['priority']}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send rerouting command: {e}")
            return False
    
    def send_power_report(self, report_data: Dict[str, Any]) -> bool:
        """Send power grid report to Kafka topic"""
        try:
            topic = self.kafka_config["topics"]["power_reports"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "report_data": report_data,
                "message_type": "power_report",
                "report_type": report_data.get("report_type", "general")
            }
            
            # Use report_id as key
            key = report_data.get("report_id", "default")
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Power report sent to {topic} - Type: {message['report_type']}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send power report: {e}")
            return False
    
    def send_grid_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send general grid alert to Kafka topic"""
        try:
            topic = self.kafka_config["topics"]["grid_alerts"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "alert_data": alert_data,
                "message_type": "grid_alert",
                "alert_type": alert_data.get("alert_type", "general"),
                "severity": alert_data.get("severity", "medium")
            }
            
            # Use alert_type as key for grouping similar alerts
            key = alert_data.get("alert_type", "general")
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Grid alert sent to {topic} - Type: {message['alert_type']}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send grid alert: {e}")
            return False
    
    def send_forecast_data(self, forecast_data: Dict[str, Any]) -> bool:
        """Send energy load forecast data"""
        try:
            topic = self.kafka_config["topics"]["energy_load"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "forecast_data": forecast_data,
                "message_type": "energy_forecast",
                "forecast_horizon": forecast_data.get("horizon_hours", 24)
            }
            
            key = forecast_data.get("zone_id", "all_zones")
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Forecast data sent to {topic}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send forecast data: {e}")
            return False
    
    def send_optimization_result(self, optimization_data: Dict[str, Any]) -> bool:
        """Send energy optimization results"""
        try:
            topic = self.kafka_config["topics"]["energy_load"]
            message = {
                "timestamp": datetime.now().isoformat(),
                "optimization_data": optimization_data,
                "message_type": "energy_optimization",
                "savings_achieved": optimization_data.get("energy_savings", 0)
            }
            
            key = optimization_data.get("zone_id", "system")
            
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Optimization result sent to {topic}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send optimization result: {e}")
            return False
    
    def flush_and_close(self):
        """Flush all pending messages and close producer"""
        try:
            if self.producer:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
                logger.info("Kafka producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.flush_and_close()

# Create singleton instance
power_producer = PowerGridKafkaProducer()