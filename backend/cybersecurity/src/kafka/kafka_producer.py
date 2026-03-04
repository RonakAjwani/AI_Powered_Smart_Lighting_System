import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from ..config.settings import config

logger = logging.getLogger(__name__)

class CybersecurityKafkaProducer:
    """
    Kafka producer for DDoS and Malware detection agents.
    Publishes DDoS alerts, malware detections, and agent results.
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
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
                compression_type=None
            )
            logger.info("Cybersecurity Kafka producer initialized (2-agent system)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def publish_ddos_attack(self, attack_type: str, severity: str, confidence: float,
                           attacker_ips: List[Dict[str, Any]], mitigation_actions: List[str],
                           attack_metrics: Dict[str, Any]) -> bool:
        """Publish DDoS attack alert"""
        try:
            message = {
                "event_type": "ddos_attack",
                "attack_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "attack_type": attack_type,
                "severity": severity,
                "confidence": confidence,
                "attacker_ips": attacker_ips,
                "mitigation_actions": mitigation_actions,
                "attack_metrics": attack_metrics,
                "source": "ddos_detection_agent"
            }
            
            key = f"ddos_{message['attack_id']}"
            
            future = self.producer.send('ddos_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.warning(f"DDoS attack published: {attack_type} (severity: {severity}, confidence: {confidence}%)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish DDoS attack: {e}")
            return False
    
    def publish_ddos_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Publish DDoS traffic metrics"""
        try:
            message = {
                "event_type": "ddos_metrics",
                "metrics_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics_data,
                "source": "ddos_detection_agent"
            }
            
            key = f"ddos_metrics_{message['metrics_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"DDoS metrics published")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish DDoS metrics: {e}")
            return False
    
    def publish_malware_detection(self, malware_type: str, malware_family: str, 
                                 infection_stage: str, severity: str, confidence: float,
                                 affected_devices: List[str], iocs: List[str],
                                 remediation_steps: List[str]) -> bool:
        """Publish malware detection alert"""
        try:
            message = {
                "event_type": "malware_detection",
                "detection_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "malware_type": malware_type,
                "malware_family": malware_family,
                "infection_stage": infection_stage,
                "severity": severity,
                "confidence": confidence,
                "affected_devices": affected_devices,
                "indicators_of_compromise": iocs,
                "remediation_steps": remediation_steps,
                "source": "malware_detection_agent"
            }
            
            key = f"malware_{message['detection_id']}"
            
            future = self.producer.send('malware_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.warning(f"Malware detection published: {malware_type}/{malware_family} (severity: {severity}, confidence: {confidence}%)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish malware detection: {e}")
            return False
    
    def publish_malware_behavior(self, device_id: str, behavioral_data: Dict[str, Any]) -> bool:
        """Publish device behavioral anomalies"""
        try:
            message = {
                "event_type": "malware_behavior",
                "behavior_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "device_id": device_id,
                "behavioral_data": behavioral_data,
                "source": "malware_detection_agent"
            }
            
            key = f"behavior_{device_id}_{message['behavior_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Malware behavior published for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish malware behavior: {e}")
            return False
    
    def publish_mitigation_actions(self, agent_name: str, actions: List[str], 
                                  severity: str, target: str) -> bool:
        """Publish mitigation/remediation actions"""
        try:
            message = {
                "event_type": "mitigation_actions",
                "action_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "actions": actions,
                "severity": severity,
                "target": target,
                "source": f"{agent_name}_agent"
            }
            
            key = f"actions_{message['action_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Mitigation actions published from {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish mitigation actions: {e}")
            return False
    
    def publish_agent_status(self, agent_name: str, status: str, metrics: Dict[str, Any]) -> bool:
        """Publish agent health status"""
        try:
            message = {
                "event_type": "agent_status",
                "status_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "status": status,
                "metrics": metrics,
                "source": f"{agent_name}_agent"
            }
            
            key = f"status_{agent_name}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Agent status published for {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish agent status: {e}")
            return False
    
    def flush(self):
        """Flush all pending messages"""
        try:
            self.producer.flush(timeout=30)
            logger.info("Producer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")
    
    def close(self):
        """Close the producer"""
        try:
            if self.producer:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
                logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
    
    def get_producer_status(self) -> Dict[str, Any]:
        """Get current producer status"""
        return {
            "producer_active": self.producer is not None,
            "agents": ["ddos_detection", "malware_detection"],
            "config": {
                "bootstrap_servers": self.kafka_config['bootstrap_servers'],
                "compression": "none",
                "acks": "all"
            },
            "timestamp": datetime.now().isoformat()
        }

# Create producer instance
cybersecurity_producer = CybersecurityKafkaProducer()