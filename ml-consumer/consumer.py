import logging
import json
import os
import requests
from confluent_kafka import Consumer, Producer
from predictor import predict  # Ensure your predictor function is available

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def start_kafka_loop(on_prediction=None):
    # Kafka Consumer configuration
    consumer_config = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP"),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': os.getenv("KAFKA_USERNAME"),
        'sasl.password': os.getenv("KAFKA_PASSWORD"),
        'group.id': 'ml-consumer-group',
        'auto.offset.reset': 'latest'
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe(["match_updates"])
    logger.info("Kafka consumer started and subscribed to topic: match_updates")

    # Kafka Producer configuration (if needed for additional use)
    producer_config = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": os.getenv("KAFKA_USERNAME"),
        "sasl.password": os.getenv("KAFKA_PASSWORD"),
    }
    producer = Producer(producer_config)

    while True:
        try:
            msg = consumer.poll(1.0)  # Poll for messages with 1-second timeout
            if msg is None:
                continue  # No message received, continue polling
            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            # Deserialize the incoming message
            try:
                data = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
                logger.error(f"Error decoding message: {e}")
                continue

            # Use the deterministic match_id provided in the message
            match_id = data.get("match_id")
            if not match_id:
                logger.error("No match_id found in the message payload.")
                continue

            logger.info(f"Received match data: {data}")

            # Run prediction logic
            try:
                prediction = predict(data)
            except Exception as e:
                logger.error(f"Error running prediction: {e}")
                prediction = "Error in prediction"

            # Prepare result to update via backend API
            result = {
                "match_id": match_id,
                "prediction": prediction
            }

            # Send the prediction update to your backend via PUT
            prediction_url = f"https://bet365-ml-api-806378004153.us-central1.run.app/prediction/{match_id}"
            try:
                response = requests.put(prediction_url, json=result)
            except Exception as e:
                logger.error(f"Error sending PUT request: {e}")
                continue

            if response.status_code == 200:
                logger.info(f"Prediction updated successfully: {response.status_code} {response.text}")
            else:
                logger.error(f"Failed to update prediction. Status: {response.status_code}, Response: {response.text}")

            # If an additional callback is provided, invoke it with the result
            if on_prediction:
                on_prediction(result)

        except Exception as e:
            # Logs any unexpected error along with stack trace
            logger.exception(f"Unexpected error in consumer loop: {e}")

if __name__ == "__main__":
    # Start the consumer loop. You can pass a callback to act on predictions if desired.
    start_kafka_loop()
