import json
import logging
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from ..config.settings import settings

class CoordinatorKafkaConsumer:
    def __init__(self, topics: list, bootstrap_servers=settings.KAFKA_BROKER_URL, group_id=settings.KAFKA_GROUP_ID):
        self.consumer = None
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.connect()

    def connect(self):
        retries = 5
        delay = 10
        for i in range(retries):
            try:
                self.consumer = KafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    client_id=settings.KAFKA_CLIENT_ID,
                    auto_offset_reset='latest',  # Start from the latest message
                    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
                )
                logging.info(f"KafkaConsumer connected and subscribed to topics: {self.topics}")
                return
            except NoBrokersAvailable:
                logging.warning(f"Kafka brokers not available. Retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
        
        logging.error("Failed to connect to Kafka after several retries.")
        raise ConnectionError("Failed to connect to Kafka consumer.")

    def consume_messages(self, callback):
        """
        Continuously poll for messages and pass them to the callback.
        
        Args:
            callback: A function to be called with (topic, message)
        """
        if not self.consumer:
            logging.error("Consumer is not initialized.")
            return
            
        logging.info("Starting to consume messages...")
        try:
            for message in self.consumer:
                try:
                    logging.info(f"Received message from topic '{message.topic}'")
                    callback(message.topic, message.value)
                except json.JSONDecodeError:
                    logging.warning(f"Could not decode message from {message.topic}: {message.value}")
                except Exception as e:
                    logging.error(f"Error processing message from {message.topic}: {e}")
        except KeyboardInterrupt:
            logging.info("Consumer shutting down...")
        finally:
            self.close()

    def close(self):
        if self.consumer:
            self.consumer.close()
            logging.info("KafkaConsumer closed.")

def get_topics_to_subscribe() -> list:
    """Helper function to get all input topics from settings."""
    return [
        settings.KAFKA_TOPIC_CYBER_ALERTS,
        settings.KAFKA_TOPIC_CYBER_REPORTS,
        settings.KAFKA_TOPIC_WEATHER_ALERTS,
        settings.KAFKA_TOPIC_WEATHER_IMPACT,
        settings.KAFKA_TOPIC_POWER_ALERTS,
        settings.KAFKA_TOPIC_POWER_FORECASTS,
        settings.KAFKA_TOPIC_POWER_OPTIMIZATION,
    ]