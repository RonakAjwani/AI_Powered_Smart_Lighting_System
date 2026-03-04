import json
import logging
from typing import Dict, Any, Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
import time
from datetime import datetime

from ..config.settings import config

# Configure logging
logger = logging.getLogger(__name__)

class PowerGridKafkaConsumer:
    """Kafka consumer for power grid management data"""
    
    def __init__(self):
        self.consumers = {}
        self.consumer_threads = {}
        self.kafka_config = config.get_kafka_config()
        self.is_running = False
        self.message_handlers = {}
    
    def _create_consumer(self, topics: list) -> KafkaConsumer:
        """Create a Kafka consumer for specific topics"""
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.kafka_config["bootstrap_servers"],
                group_id=self.kafka_config["consumer_group"],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000
            )
            logger.info(f"Created consumer for topics: {topics}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            raise
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a message handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def start_energy_load_consumer(self):
        """Start consumer for energy load data"""
        topic = self.kafka_config["topics"]["energy_load"]
        
        def consume_energy_load():
            consumer = self._create_consumer([topic])
            logger.info(f"Started energy load consumer for topic: {topic}")
            
            try:
                for message in consumer:
                    if not self.is_running:
                        break
                    
                    try:
                        data = message.value
                        message_type = data.get("message_type", "unknown")
                        
                        # Handle different energy load message types
                        if message_type == "energy_load":
                            self._handle_energy_load_data(data)
                        elif message_type == "energy_forecast":
                            self._handle_forecast_data(data)
                        elif message_type == "energy_optimization":
                            self._handle_optimization_result(data)
                        
                        # Call registered handler if exists
                        if message_type in self.message_handlers:
                            self.message_handlers[message_type](data)
                            
                    except Exception as e:
                        logger.error(f"Error processing energy load message: {e}")
                        
            except Exception as e:
                logger.error(f"Energy load consumer error: {e}")
            finally:
                consumer.close()
        
        thread = threading.Thread(target=consume_energy_load, daemon=True)
        self.consumer_threads["energy_load"] = thread
        thread.start()
    
    def start_outage_consumer(self):
        """Start consumer for power outage alerts"""
        topic = self.kafka_config["topics"]["power_outage"]
        
        def consume_outages():
            consumer = self._create_consumer([topic])
            logger.info(f"Started outage consumer for topic: {topic}")
            
            try:
                for message in consumer:
                    if not self.is_running:
                        break
                    
                    try:
                        data = message.value
                        self._handle_outage_alert(data)
                        
                        # Call registered handler if exists
                        if "power_outage" in self.message_handlers:
                            self.message_handlers["power_outage"](data)
                            
                    except Exception as e:
                        logger.error(f"Error processing outage message: {e}")
                        
            except Exception as e:
                logger.error(f"Outage consumer error: {e}")
            finally:
                consumer.close()
        
        thread = threading.Thread(target=consume_outages, daemon=True)
        self.consumer_threads["outage"] = thread
        thread.start()
    
    def start_rerouting_consumer(self):
        """Start consumer for energy rerouting commands"""
        topic = self.kafka_config["topics"]["energy_rerouting"]
        
        def consume_rerouting():
            consumer = self._create_consumer([topic])
            logger.info(f"Started rerouting consumer for topic: {topic}")
            
            try:
                for message in consumer:
                    if not self.is_running:
                        break
                    
                    try:
                        data = message.value
                        self._handle_rerouting_command(data)
                        
                        # Call registered handler if exists
                        if "energy_rerouting" in self.message_handlers:
                            self.message_handlers["energy_rerouting"](data)
                            
                    except Exception as e:
                        logger.error(f"Error processing rerouting message: {e}")
                        
            except Exception as e:
                logger.error(f"Rerouting consumer error: {e}")
            finally:
                consumer.close()
        
        thread = threading.Thread(target=consume_rerouting, daemon=True)
        self.consumer_threads["rerouting"] = thread
        thread.start()
    
    def start_grid_alerts_consumer(self):
        """Start consumer for general grid alerts"""
        topic = self.kafka_config["topics"]["grid_alerts"]
        
        def consume_alerts():
            consumer = self._create_consumer([topic])
            logger.info(f"Started grid alerts consumer for topic: {topic}")
            
            try:
                for message in consumer:
                    if not self.is_running:
                        break
                    
                    try:
                        data = message.value
                        self._handle_grid_alert(data)
                        
                        # Call registered handler if exists
                        if "grid_alert" in self.message_handlers:
                            self.message_handlers["grid_alert"](data)
                            
                    except Exception as e:
                        logger.error(f"Error processing grid alert: {e}")
                        
            except Exception as e:
                logger.error(f"Grid alerts consumer error: {e}")
            finally:
                consumer.close()
        
        thread = threading.Thread(target=consume_alerts, daemon=True)
        self.consumer_threads["alerts"] = thread
        thread.start()
    
    def _handle_energy_load_data(self, data: Dict[str, Any]):
        """Handle energy load data messages"""
        zone_id = data.get("zone_id", "unknown")
        load_data = data.get("load_data", {})
        timestamp = data.get("timestamp")
        
        logger.info(f"Received energy load data for zone {zone_id} at {timestamp}")
        
        # Process load data (implement specific logic as needed)
        current_load = load_data.get("current_load", 0)
        voltage = load_data.get("voltage", 0)
        
        if voltage < config.LOW_VOLTAGE_THRESHOLD:
            logger.warning(f"Low voltage detected in zone {zone_id}: {voltage}")
    
    def _handle_forecast_data(self, data: Dict[str, Any]):
        """Handle energy forecast data messages"""
        forecast_data = data.get("forecast_data", {})
        horizon = data.get("forecast_horizon", 24)
        
        logger.info(f"Received forecast data with {horizon}h horizon")
        
        # Process forecast data
        zone_id = forecast_data.get("zone_id", "all")
        predicted_load = forecast_data.get("predicted_load", [])
        
        logger.debug(f"Forecast for zone {zone_id}: {len(predicted_load)} data points")
    
    def _handle_optimization_result(self, data: Dict[str, Any]):
        """Handle energy optimization results"""
        optimization_data = data.get("optimization_data", {})
        savings = data.get("savings_achieved", 0)
        
        logger.info(f"Received optimization result: {savings}% energy savings")
        
        # Process optimization results
        zone_id = optimization_data.get("zone_id", "system")
        new_settings = optimization_data.get("new_settings", {})
        
        logger.debug(f"Optimization applied to zone {zone_id}")
    
    def _handle_outage_alert(self, data: Dict[str, Any]):
        """Handle power outage alerts"""
        outage_data = data.get("outage_data", {})
        severity = data.get("severity", "medium")
        timestamp = data.get("timestamp")
        
        logger.warning(f"OUTAGE ALERT - Severity: {severity} at {timestamp}")
        
        # Process outage alert
        affected_zones = outage_data.get("affected_zones", [])
        outage_type = outage_data.get("outage_type", "unknown")
        
        for zone in affected_zones:
            logger.error(f"Zone {zone} affected by {outage_type} outage")
    
    def _handle_rerouting_command(self, data: Dict[str, Any]):
        """Handle energy rerouting commands"""
        rerouting_data = data.get("rerouting_data", {})
        priority = data.get("priority", "medium")
        timestamp = data.get("timestamp")
        
        logger.info(f"REROUTING COMMAND - Priority: {priority} at {timestamp}")
        
        # Process rerouting command
        command_id = rerouting_data.get("command_id", "unknown")
        source_zones = rerouting_data.get("source_zones", [])
        target_zones = rerouting_data.get("target_zones", [])
        
        logger.info(f"Command {command_id}: Rerouting from {source_zones} to {target_zones}")
    
    def _handle_grid_alert(self, data: Dict[str, Any]):
        """Handle general grid alerts"""
        alert_data = data.get("alert_data", {})
        alert_type = data.get("alert_type", "general")
        severity = data.get("severity", "medium")
        timestamp = data.get("timestamp")
        
        logger.info(f"GRID ALERT - Type: {alert_type}, Severity: {severity} at {timestamp}")
        
        # Process grid alert
        message = alert_data.get("message", "No details available")
        affected_components = alert_data.get("affected_components", [])
        
        logger.info(f"Alert message: {message}")
        if affected_components:
            logger.info(f"Affected components: {affected_components}")
    
    def start_all_consumers(self):
        """Start all Kafka consumers"""
        self.is_running = True
        
        try:
            self.start_energy_load_consumer()
            self.start_outage_consumer()
            self.start_rerouting_consumer()
            self.start_grid_alerts_consumer()
            
            logger.info("All power grid consumers started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start consumers: {e}")
            self.stop_all_consumers()
            raise
    
    def stop_all_consumers(self):
        """Stop all Kafka consumers"""
        self.is_running = False
        
        # Wait for threads to finish
        for thread_name, thread in self.consumer_threads.items():
            if thread.is_alive():
                logger.info(f"Stopping {thread_name} consumer...")
                thread.join(timeout=5)
        
        self.consumer_threads.clear()
        logger.info("All power grid consumers stopped")
    
    def get_consumer_status(self) -> Dict[str, bool]:
        """Get status of all consumers"""
        status = {}
        for thread_name, thread in self.consumer_threads.items():
            status[thread_name] = thread.is_alive() if thread else False
        return status

# Create singleton instance
power_consumer = PowerGridKafkaConsumer()