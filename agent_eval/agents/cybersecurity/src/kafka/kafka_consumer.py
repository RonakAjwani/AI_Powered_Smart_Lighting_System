import json
import logging
import threading
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from ..config.settings import config
from ..graph.cybersecurity_graph import cybersecurity_graph

logger = logging.getLogger(__name__)

class CybersecurityKafkaConsumer:
    """
    Kafka consumer for DDoS and Malware detection agents.
    Listens to network and device events for the 2-agent system.
    """
    
    def __init__(self):
        self.kafka_config = config.get_kafka_config()
        self.consumer = None
        self.is_running = False
        self.consumer_thread = None
        
        # Topics to monitor (2-agent system)
        self.topics = [
            'network_events',
            'device_events',
            'cyber_alerts'
        ]
        
        # Message handlers for DDoS and Malware events
        self.handlers = {
            'network_traffic': self._handle_ddos_event,
            'http_request': self._handle_ddos_event,
            'connection_attempt': self._handle_ddos_event,
            'device_behavior': self._handle_malware_event,
            'file_system_change': self._handle_malware_event,
            'network_connection': self._handle_malware_event,
            'process_execution': self._handle_malware_event,
            'firmware_check': self._handle_malware_event
        }
    
    def _create_consumer(self):
        """Create Kafka consumer instance"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                group_id=self.kafka_config.get('consumer_group', 'cybersecurity_agents'),
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
                max_poll_records=100
            )
            logger.info(f"Kafka consumer created for 2-agent system. Topics: {self.topics}")
            
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    def start_consuming(self):
        """Start consuming messages in a separate thread"""
        if self.is_running:
            logger.warning("Consumer is already running")
            return
        
        try:
            self._create_consumer()
            self.is_running = True
            
            # Start consumer thread
            self.consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
            self.consumer_thread.start()
            
            logger.info("Cybersecurity Kafka consumer started")
            
        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
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
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
        
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
            logger.info("Consumer thread stopped")
    
    def _consume_messages(self):
        """Main message consumption loop"""
        logger.info("Starting message consumption loop")
        
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
                            logger.error(f"Error processing message: {e}")
                            continue
                
            except KafkaError as e:
                logger.error(f"Kafka error during consumption: {e}")
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Unexpected error in consumption loop: {e}")
                time.sleep(1)
        
        logger.info("Message consumption loop ended")
    
    def _process_message(self, message):
        """Process individual Kafka message"""
        try:
            # Extract message data
            topic = message.topic
            key = message.key
            value = message.value
            timestamp = datetime.fromtimestamp(message.timestamp / 1000)
            
            logger.debug(f"Processing message from topic {topic}: {key}")
            
            # Validate message structure
            if not isinstance(value, dict):
                logger.warning(f"Invalid message format from {topic}: {type(value)}")
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
            logger.error(f"Error processing message: {e}")
    
    def _handle_ddos_event(self, data: Dict[str, Any]):
        """Handle DDoS detection events (network traffic, HTTP requests, connections)"""
        logger.info(f"DDoS event received: {data.get('event_type', 'unknown')}")
        
        severity = data.get('severity', 'low')
        
        # Trigger DDoS analysis for suspicious patterns
        if severity in ['high', 'critical'] or data.get('suspicious', False):
            try:
                result = cybersecurity_graph.execute_targeted_analysis("ddos")
                logger.info(f"DDoS analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in DDoS analysis: {e}")
        
        self._log_event("ddos_detection", data)
    
    def _handle_malware_event(self, data: Dict[str, Any]):
        """Handle malware detection events (device behavior, file changes, processes)"""
        logger.info(f"Malware event received: {data.get('event_type', 'unknown')}")
        
        severity = data.get('severity', 'low')
        
        # Trigger malware analysis for suspicious behavior
        if severity in ['high', 'critical'] or data.get('suspicious', False):
            try:
                result = cybersecurity_graph.execute_targeted_analysis("malware")
                logger.info(f"Malware analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in malware analysis: {e}")
        
        self._log_event("malware_detection", data)
    
    def _handle_security_alert(self, data: Dict[str, Any]):
        """Handle security alert events"""
        logger.info(f"Security alert received: {data.get('severity', 'unknown')} severity")
        
        severity = data.get('severity', 'low')
        
        # Trigger appropriate response based on severity
        if severity in ['critical', 'high']:
            # Immediate response required
            try:
                result = cybersecurity_graph.execute_cybersecurity_analysis()
                logger.info(f"Emergency analysis triggered: {result.get('risk_level', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in emergency analysis: {e}")
        else:
            # Standard monitoring
            self._log_event("security_alert", data)
    
    def _handle_sensor_data(self, data: Dict[str, Any]):
        """Handle sensor data events"""
        logger.debug(f"Sensor data received from: {data.get('source_id', 'unknown')}")
        
        # Check for integrity issues
        if data.get('checksum_failed', False) or data.get('tampered', False):
            logger.warning("Data integrity issue detected in sensor data")
            
            try:
                # Trigger integrity-focused analysis
                result = cybersecurity_graph.execute_targeted_analysis("integrity")
                logger.info(f"Integrity analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in integrity analysis: {e}")
        
        self._log_event("sensor_data", data)
    
    def _handle_network_traffic(self, data: Dict[str, Any]):
        """Handle network traffic events"""
        logger.debug(f"Network traffic from: {data.get('source_ip', 'unknown')}")
        
        # Check for suspicious activity
        if data.get('suspicious', False) or data.get('severity') in ['high', 'critical']:
            logger.info("Suspicious network activity detected")
            
            try:
                # Trigger intrusion response
                result = cybersecurity_graph.execute_targeted_analysis("intrusion")
                logger.info(f"Intrusion analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in intrusion analysis: {e}")
        
        self._log_event("network_traffic", data)
    
    def _handle_threat_detection(self, data: Dict[str, Any]):
        """Handle threat detection events"""
        logger.info(f"Threat detected: {data.get('threat_type', 'unknown')}")
        
        threat_type = data.get('threat_type', '')
        confidence = data.get('confidence', 'low')
        
        # Trigger threat-focused analysis for high confidence threats
        if confidence in ['high', 'critical']:
            try:
                result = cybersecurity_graph.execute_targeted_analysis("threats")
                logger.info(f"Threat analysis result: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Error in threat analysis: {e}")
        
        self._log_event("threat_detection", data)
    
    def _handle_integrity_violation(self, data: Dict[str, Any]):
        """Handle data integrity violation events"""
        logger.warning(f"Data integrity violation: {data.get('violation_type', 'unknown')}")
        
        try:
            # Always trigger integrity analysis for violations
            result = cybersecurity_graph.execute_targeted_analysis("integrity")
            logger.info(f"Integrity violation analysis: {result.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Error in integrity violation analysis: {e}")
        
        self._log_event("integrity_violation", data)
    
    def _handle_generic_event(self, data: Dict[str, Any]):
        """Handle generic/unknown events"""
        event_type = data.get('event_type', 'unknown')
        logger.debug(f"Generic event received: {event_type}")
        
        self._log_event("generic", data)
    
    def _log_event(self, event_category: str, data: Dict[str, Any]):
        """Log event for monitoring and debugging"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "category": event_category,
                "event_type": data.get('event_type', 'unknown'),
                "source": data.get('source_id', 'unknown'),
                "severity": data.get('severity', 'low')
            }
            
            # You could also send this to a logging service or database
            logger.debug(f"Event logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def get_consumer_status(self) -> Dict[str, Any]:
        """Get current consumer status"""
        return {
            "is_running": self.is_running,
            "system": "2-agent (DDoS + Malware)",
            "topics": self.topics,
            "thread_alive": self.consumer_thread.is_alive() if self.consumer_thread else False,
            "consumer_active": self.consumer is not None,
            "timestamp": datetime.now().isoformat()
        }

# Create consumer instance
cybersecurity_consumer = CybersecurityKafkaConsumer()