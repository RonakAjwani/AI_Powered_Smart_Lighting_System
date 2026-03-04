import json
import logging
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from ..config.settings import settings

class CoordinatorKafkaProducer:
    def __init__(self, bootstrap_servers=settings.KAFKA_BROKER_URL, client_id=settings.KAFKA_CLIENT_ID):
        self.producer = None
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.connect()

    def connect(self):
        retries = 5
        delay = 10  # seconds
        for i in range(retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    client_id=self.client_id,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Ensure messages are received by all replicas
                    retries=3
                )
                logging.info(f"KafkaProducer connected successfully to {self.bootstrap_servers}")
                self.publish_system_log("CoordinatorKafkaProducer connected.")
                return
            except NoBrokersAvailable:
                logging.warning(f"Kafka brokers not available. Retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
        
        logging.error("Failed to connect to Kafka after several retries. Exiting.")
        # In a real app, you might raise an exception or exit
        # For this example, we'll set producer to None and let publish fail
        self.producer = None
        
    def publish(self, topic, message):
        if not self.producer:
            logging.error("KafkaProducer is not connected. Cannot publish message.")
            return
            
        try:
            logging.info(f"Publishing message to topic '{topic}': {message}")
            future = self.producer.send(topic, message)
            # Block for 'synchronous' sends
            record_metadata = future.get(timeout=10)
            logging.info(f"Message published to {record_metadata.topic} partition {record_metadata.partition}")
        except Exception as e:
            logging.error(f"Error publishing message to Kafka: {e}")
            # Attempt to reconnect
            self.connect()

    def publish_system_log(self, message: str):
        log_message = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": "coordinator-agent",
            "level": "INFO",
            "message": message
        }
        self.publish(settings.KAFKA_SYSTEM_LOGS_TOPIC, log_message)

    def close(self):
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logging.info("KafkaProducer flushed and closed.")

# Singleton instance
kafka_producer = CoordinatorKafkaProducer()