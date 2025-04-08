import json
import os
import requests
from confluent_kafka import Consumer, Producer
from predictor import predict  # Ensure your predictor function is available

def start_kafka_loop(on_prediction=None):
    # Kafka Consumer configuration
    consumer_config = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": os.getenv("KAFKA_USERNAME"),
        "sasl.password": os.getenv("KAFKA_PASSWORD"),
        "group.id": "ml-consumer-group",
        "auto.offset.reset": "latest"
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe(["match_updates"])
    print("Kafka consumer started and subscribed to topic: match_updates")

    # Kafka Producer configuration (if needed)
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
            msg = consumer.poll(1.0)
            if msg is None:
                continue  # No message received, continue polling
            if msg.error():
                print("Kafka error:", msg.error())
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
            except Exception as e:
                print("Error decoding message:", e)
                continue

            # Use the deterministic match_id from the message (from the backend)
            match_id = data.get("match_id")
            if not match_id:
                print("No match_id found in the message payload.")
                continue

            print("Received match data:", data)

            try:
                prediction = predict(data)
            except Exception as e:
                print("Error running prediction:", e)
                prediction = "Error in prediction"

            # Prepare result to update via backend API
            result = {
                "match_id": match_id,
                "prediction": prediction
            }

            prediction_url = f"https://bet365-ml-api-806378004153.us-central1.run.app/prediction/{match_id}"
            try:
                response = requests.put(prediction_url, json=result)
            except Exception as e:
                print("Error sending PUT request:", e)
                continue

            if response.status_code == 200:
                print("Prediction updated successfully:", response.status_code, response.text)
            else:
                print(f"Failed to update prediction. Status: {response.status_code}, Response: {response.text}")

            if on_prediction:
                on_prediction(result)

        except Exception as e:
            print("Unexpected error in consumer loop:", e)

if __name__ == "__main__":
    start_kafka_loop()
