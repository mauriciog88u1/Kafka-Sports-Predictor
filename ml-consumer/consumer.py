from confluent_kafka import Consumer, Producer
import json
import requests
import os
from predictor import predict  # Assuming this function is defined elsewhere and works correctly

def start_kafka_loop(on_prediction=None):
    # Kafka Consumer configuration
    consumer_config = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP"),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv("KAFKA_USERNAME"),
        'sasl.password': os.getenv("KAFKA_PASSWORD"),
        'group.id': 'ml-consumer-group',
        'auto.offset.reset': 'latest'
    }

    # Kafka Consumer instance
    consumer = Consumer(consumer_config)
    consumer.subscribe(["match_updates"])  # Listening to "match_updates" topic

    print("Kafka consumer started and listening on topic: match_updates")

    # Kafka Producer instance for sending predictions back (if needed)
    producer = Producer({
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": os.getenv("KAFKA_USERNAME"),
        "sasl.password": os.getenv("KAFKA_PASSWORD"),
    })

    while True:
        # Poll the Kafka topic for messages (1-second timeout)
        msg = consumer.poll(1.0)

        if msg is None:
            continue  # No message received, continue to poll
        if msg.error():
            print(f"⚠️ Kafka error: {msg.error()}")
            continue  # Handle any Kafka errors

        try:
            # Deserialize the incoming message (match data)
            data = json.loads(msg.value().decode("utf-8"))
            match_id = data["idEvent"]  # Using the event ID (assuming it's the match ID)
            print("📦 Match received:", data)

            # Make the prediction based on the match data
            prediction = predict(data)

            # Prepare the result to send back (send prediction to producer or UI)
            result = {
                "match_id": match_id,
                "prediction": prediction
            }

            # Define the URL where the prediction should be sent (this would be the API that handles predictions)
            prediction_url = f"https://bet365-ml-api-806378004153.us-central1.run.app/prediction/{match_id}"

            # Send the prediction result to the producer via PUT request (or POST if needed)
            response = requests.put(prediction_url, json=result)

            # Log the response from the PUT request
            if response.status_code == 200:
                print("📈 Prediction sent successfully:", response.status_code, response.text)
            else:
                print(f"❌ Failed to send prediction. Status: {response.status_code}, Response: {response.text}")

            # If the callback `on_prediction` was passed, invoke it
            if on_prediction:
                on_prediction(result)

        except Exception as e:
            print(f"❌ Error during prediction: {e}")
