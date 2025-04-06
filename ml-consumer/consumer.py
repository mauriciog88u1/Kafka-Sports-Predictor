from confluent_kafka import Consumer

from predictor import predict
import os
import json
import sys

print("Kafka config (sanitized):", file=sys.stderr)
print("  bootstrap:", os.getenv("KAFKA_BOOTSTRAP"), file=sys.stderr)
print("  username:", os.getenv("KAFKA_USERNAME"), file=sys.stderr)
print("  password:", "******" if os.getenv("KAFKA_PASSWORD") else "MISSING", file=sys.stderr)

def start_kafka_loop(on_prediction=None):
    print("Starting Kafka consumer...")
    conf = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP"),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv("KAFKA_USERNAME"),
        'sasl.password': os.getenv("KAFKA_PASSWORD"),
        'group.id': 'ml-consumer-group',
        'auto.offset.reset': 'latest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(["match_updates"])

    print("Kafka consumer started and listening on topic: match_updates")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"⚠️ Kafka error: {msg.error()}")
            continue

        try:
            data = json.loads(msg.value().decode("utf-8"))
            print("📦 Match received:", data)

            prediction = predict(data)
            print("📈 Prediction:", prediction)

            if on_prediction:
                on_prediction(prediction)

        except Exception as e:
            print(f"❌ Error during prediction: {e}")
