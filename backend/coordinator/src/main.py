import logging
import threading
import time
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator

from .config.settings import settings
from .kafka.kafka_consumer import CoordinatorKafkaConsumer, get_topics_to_subscribe
from .kafka.kafka_producer import kafka_producer
from .graph.coordinator_graph import coordinator_graph

# --- Logging Configuration ---
# REMOVED basicConfig. We will use Uvicorn's logger.
logger = logging.getLogger("uvicorn.error") # <-- THIS IS THE FIX

# --- System State ---
# This dictionary will hold the *latest* known state.
# It needs to be thread-safe.
system_state = {}
state_lock = threading.Lock()

# --- Kafka Consumer & Processing ---
def process_kafka_message(topic: str, message: dict):
    """
    Callback function for the Kafka consumer.
    Updates the system state.
    """
    logger.info(f"Processing message from topic: {topic}")
    
    with state_lock:
        if topic == settings.KAFKA_TOPIC_CYBER_ALERTS:
            # Alerts are likely lists
            if 'cyber_alerts' not in system_state:
                system_state['cyber_alerts'] = []
            system_state['cyber_alerts'].append(message)
            # Optional: Prune old alerts
            system_state['cyber_alerts'] = system_state['cyber_alerts'][-5:] 
            
        elif topic == settings.KAFKA_TOPIC_CYBER_REPORTS:
            system_state['cyber_reports'] = [message] # Store latest report
            
        elif topic == settings.KAFKA_TOPIC_WEATHER_ALERTS:
            if 'weather_alerts' not in system_state:
                system_state['weather_alerts'] = []
            system_state['weather_alerts'].append(message)
            system_state['weather_alerts'] = system_state['weather_alerts'][-5:]
            
        elif topic == settings.KAFKA_TOPIC_WEATHER_IMPACT:
            system_state['weather_impact'] = message # Store latest analysis
            
        elif topic == settings.KAFKA_TOPIC_POWER_ALERTS:
            if 'power_alerts' not in system_state:
                system_state['power_alerts'] = []
            system_state['power_alerts'].append(message)
            system_state['power_alerts'] = system_state['power_alerts'][-5:]
            
        elif topic == settings.KAFKA_TOPIC_POWER_FORECASTS:
            system_state['power_forecasts'] = message # Store latest forecast
            
        elif topic == settings.KAFKA_TOPIC_POWER_OPTIMIZATION:
            system_state['power_optimization'] = message # Store latest optimization
        
        else:
            logger.warning(f"Received message from unhandled topic: {topic}")

def run_decision_loop():
    """
    A separate thread that periodically runs the coordinator graph
    based on the current system state.
    """
    logger.info("--- Decision loop thread started. ---") 
    decision_interval_seconds = 10 
    
    while True:
        try:
            time.sleep(decision_interval_seconds)
            logger.info("--- Decision loop awake, checking state... ---") 
            
            # Create a copy of the state for the graph
            with state_lock:
                if not system_state:
                    logger.info("System state is empty, skipping decision loop.")
                    continue
                current_state_snapshot = system_state.copy()
            
            logger.info("--- Triggering Coordinator Graph ---")
            
            # Prepare input for the graph
            # The graph expects all keys to be present
            graph_input = {
                "cyber_alerts": current_state_snapshot.get("cyber_alerts", []),
                "cyber_reports": current_state_snapshot.get("cyber_reports", []),
                "weather_alerts": current_state_snapshot.get("weather_alerts", []),
                "weather_impact": current_state_snapshot.get("weather_impact", {}),
                "power_alerts": current_state_snapshot.get("power_alerts", []),
                "power_forecasts": current_state_snapshot.get("power_forecasts", {}),
                "power_optimization": current_state_snapshot.get("power_optimization", {}),
                "primary_concern": None,
                "final_command": None
            }

            # Invoke the graph
            result = coordinator_graph.invoke(graph_input)
            final_command = result.get("final_command")
            
            if final_command and "error" not in final_command:
                logger.info(f"Publishing new coordinator command: {final_command}")
                kafka_producer.publish(
                    settings.KAFKA_TOPIC_COORDINATOR_COMMANDS, 
                    final_command
                )
            else:
                logger.error(f"Graph execution failed or produced an error command: {final_command}")

            # Clear state *after* processing
            with state_lock:
                system_state.clear()
                logger.info("System state cleared for next decision cycle.")

        except Exception as e:
            logger.error(f"Error in decision loop: {e}", exc_info=True)
        except KeyboardInterrupt:
            logger.info("Decision loop shutting down.")
            break

def start_kafka_consumer():
    """Initializes and runs the Kafka consumer in a separate thread."""
    try:
        logger.info("--- Kafka consumer thread started. ---") 
        topics = get_topics_to_subscribe()
        logger.info(f"--- Subscribing to topics: {topics} ---") 
        consumer = CoordinatorKafkaConsumer(topics=topics)
        consumer.consume_messages(callback=process_kafka_message)
    except ConnectionError:
        logger.error("Failed to start Kafka consumer. Application will not process messages.")
    except Exception as e:
        logger.error(f"Unhandled exception in Kafka consumer thread: {e}", exc_info=True)

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for FastAPI lifespan events.
    Handles startup and shutdown.
    """
    logger.info("--- Coordinator Agent starting up (lifespan event) ---") 
    kafka_producer.publish_system_log("Coordinator Agent starting up.")
    
    # Start Kafka consumer in a background thread
    logger.info("--- Starting Kafka consumer thread... ---") 
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Start Decision loop in a background thread
    logger.info("--- Starting decision loop thread... ---") 
    decision_thread = threading.Thread(target=run_decision_loop, daemon=True)
    decision_thread.start()
    
    yield
    
    # --- Shutdown logic ---
    logger.info("--- Coordinator Agent shutting down (lifespan event) ---") 
    kafka_producer.publish_system_log("Coordinator Agent shutting down.")
    kafka_producer.close()
    # Consumer thread is daemon, will exit with main thread

app = FastAPI(
    title="Coordinator Agent",
    description="The central AI coordinator for the Smart Lighting System.",
    version="1.0.0",
    lifespan=lifespan
)

# This creates the /metrics endpoint for Prometheus
Instrumentator().instrument(app).expose(app)

@app.get("/", summary="Root Endpoint")
def read_root():
    return {"message": "Coordinator Agent is running."}

@app.get("/health", summary="Health Check")
def health_check():
    """Provides a simple health check endpoint."""
    # TODO: Add check for Kafka connection
    return {"status": "ok"}

@app.get("/state", summary="Get Current S_tat_e")
def get_current_state():
    """Returns the last known aggregated system state."""
    with state_lock:
        return system_state.copy()

if __name__ == "__main__":
    import uvicorn
    # This block is not run when using Docker
    uvicorn.run(app, host="0.0.0.0", port=8004)