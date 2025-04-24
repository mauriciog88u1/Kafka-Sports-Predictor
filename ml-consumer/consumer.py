import json
import os
import signal
import time
import requests
from typing import Dict, List, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
from predictor import predict
from dotenv import load_dotenv
import logging
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ml-consumer')

# Consumer configuration
BATCH_SIZE = 10  # Number of messages to process in a batch
MAX_POLL_INTERVAL = 300  # Maximum time (in seconds) between polls
POLL_TIMEOUT = 1.0  # Timeout for each poll (in seconds)
MAX_RETRIES = 3  # Maximum number of retries for failed predictions
BACKOFF_FACTOR = 2  # Exponential backoff factor

class MLConsumer:
    def __init__(self):
        self.running = True
        self.consumer = None
        self.api_url = None
        self.health_status = {
            "service": "ml-consumer",
            "status": "starting",
            "last_processed_time": None,
            "messages_processed": 0,
            "errors": 0,
            "last_error": None,
            "last_message": None
        }
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)

    def load_environment(self) -> bool:
        """Load environment variables and validate configuration"""
        try:
            env = os.getenv("ENVIRONMENT", "development")
            env_file = f".env.{env}"
            
            if os.path.exists(env_file):
                load_dotenv(env_file)
                logger.info(f"Loaded environment from {env_file}")
            
            # Required environment variables
            required_vars = ["KAFKA_BOOTSTRAP", "KAFKA_USERNAME", "KAFKA_PASSWORD", "API_URL"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            # Ensure API URL ends with /api
            self.api_url = os.getenv("API_URL").rstrip('/')
            if not self.api_url.endswith('/api'):
                self.api_url += '/api'
            return True
            
        except Exception as e:
            logger.error(f"Error loading environment: {str(e)}")
            return False

    def initialize_consumer(self) -> bool:
        """Initialize the Kafka consumer with configuration"""
        try:
            config = {
                "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
                "security.protocol": "SASL_SSL",
                "sasl.mechanisms": "PLAIN",
                "sasl.username": os.getenv("KAFKA_USERNAME"),
                "sasl.password": os.getenv("KAFKA_PASSWORD"),
                "group.id": "ml-consumer-group",
                "auto.offset.reset": "latest",
                "enable.auto.commit": False,  # Manual commit for better control
                "max.poll.interval.ms": MAX_POLL_INTERVAL * 1000,
                "session.timeout.ms": 45000,
                "heartbeat.interval.ms": 15000
            }
            
            self.consumer = Consumer(config)
            self.consumer.subscribe(["match_updates"])
            logger.info("Kafka consumer initialized and subscribed to topic: match_updates")
            self.health_status["status"] = "running"
            return True
            
        except Exception as e:
            logger.error(f"Error initializing consumer: {str(e)}")
            self.health_status["status"] = "error"
            self.health_status["last_error"] = str(e)
            return False

    def process_batch(self, messages: List[Dict]) -> None:
        """Process a batch of messages with retries and backoff"""
        for message_data in messages:
            match_id = message_data.get("match_id")
            if not match_id:
                logger.error("Message missing match_id field")
                continue
            
            for attempt in range(MAX_RETRIES):
                try:
                    # Run prediction
                    prediction = predict(message_data)
                    
                    # Update prediction via API
                    result = {
                        "prediction": prediction
                    }
                    
                    response = requests.put(
                        f"{self.api_url}/prediction/{match_id}",
                        json=result,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully processed match_id: {match_id}")
                        self.health_status["messages_processed"] += 1
                        self.health_status["last_processed_time"] = time.time()
                        self.health_status["last_message"] = {
                            "match_id": match_id,
                            "prediction": prediction
                        }
                        break
                    else:
                        logger.warning(f"Failed to update prediction for match_id {match_id}. Status: {response.status_code}, Response: {response.text}")
                        
                except Exception as e:
                    logger.error(f"Error processing match_id {match_id}: {str(e)}")
                    self.health_status["errors"] += 1
                    self.health_status["last_error"] = str(e)
                    
                    if attempt < MAX_RETRIES - 1:
                        sleep_time = BACKOFF_FACTOR ** attempt
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Max retries reached for match_id {match_id}")

    def shutdown_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received, closing consumer...")
        self.running = False

    def run(self):
        """Main consumer loop with batch processing"""
        if not self.load_environment():
            return
        
        if not self.initialize_consumer():
            return
        
        try:
            batch = []
            last_commit = time.time()
            
            while self.running:
                try:
                    msg = self.consumer.poll(POLL_TIMEOUT)
                    
                    if msg is None:
                        # No message, process any remaining messages in batch
                        if batch:
                            self.process_batch(batch)
                            batch = []
                            self.consumer.commit()
                            last_commit = time.time()
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            logger.debug("Reached end of partition")
                        else:
                            logger.error(f"Kafka error: {msg.error()}")
                        continue
                    
                    try:
                        message_data = json.loads(msg.value().decode("utf-8"))
                        batch.append(message_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding message: {str(e)}")
                        continue
                    
                    # Process batch if full or if enough time has passed
                    if len(batch) >= BATCH_SIZE or (time.time() - last_commit) > MAX_POLL_INTERVAL/2:
                        self.process_batch(batch)
                        batch = []
                        self.consumer.commit()
                        last_commit = time.time()
                    
                except Exception as e:
                    logger.error(f"Error in consumer loop: {str(e)}")
                    self.health_status["errors"] += 1
                    self.health_status["last_error"] = str(e)
                    time.sleep(1)  # Prevent tight error loop
            
        finally:
            # Clean shutdown
            try:
                if batch:
                    self.process_batch(batch)
                if self.consumer:
                    self.consumer.commit()
                    self.consumer.close()
                logger.info("Consumer closed successfully")
            except Exception as e:
                logger.error(f"Error during shutdown: {str(e)}")

def start_kafka_loop(on_prediction=None):
    """Start the Kafka consumer"""
    consumer = MLConsumer()
    consumer.run()

if __name__ == "__main__":
    start_kafka_loop()



