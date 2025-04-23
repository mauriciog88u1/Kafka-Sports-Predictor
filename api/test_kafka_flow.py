import requests
import json
import time
import subprocess
import sys
import os
from pprint import pprint

BASE_URL = "http://localhost:8000"

def start_consumer():
    """Start the Kafka consumer in a separate process"""
    # Get the absolute path to the consumer script
    consumer_path = os.path.join(os.path.dirname(__file__), "..", "ml-consumer", "consumer.py")
    consumer_dir = os.path.dirname(consumer_path)
    
    print(f"\n=== Consumer Debug ===")
    print(f"Consumer script path: {consumer_path}")
    print(f"Consumer directory: {consumer_dir}")
    print(f"Consumer script exists: {os.path.exists(consumer_path)}")
    
    # Create environment with current directory set to consumer directory
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["PYTHONPATH"] = consumer_dir
    
    return subprocess.Popen(
        [sys.executable, consumer_path],
        env=env,
        cwd=consumer_dir
    )

def test_prediction_flow():
    print("\n=== Testing Complete Prediction Flow ===")
    
    # 1. Get a match
    print("\n1. Getting a match...")
    response = requests.get(f"{BASE_URL}/matches", params={"team_id": "133602"})
    if response.status_code != 200:
        print("Failed to get matches")
        return
        
    matches = response.json().get("matches", [])
    if not matches:
        print("No matches found")
        return
        
    match = matches[0]
    print("Selected match:", match["strEvent"])
    
    # 2. Send prediction request
    print("\n2. Sending prediction request...")
    predict_response = requests.post(f"{BASE_URL}/predict", json=match)
    if predict_response.status_code != 200:
        print("Failed to send prediction request")
        return
        
    predict_data = predict_response.json()
    print("Prediction request sent:", predict_data)
    
    # 3. Poll for prediction result
    print("\n3. Polling for prediction result...")
    match_id = predict_data["correlation_id"]
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        result_response = requests.get(f"{BASE_URL}/prediction/{match_id}")
        if result_response.status_code == 200:
            result = result_response.json()
            print(f"Attempt {attempt + 1}:", result)
            
            if result["prediction"] != "waiting for prediction...":
                print("\nPrediction received:", result["prediction"])
                return
                
        time.sleep(2)
        attempt += 1
        
    print("\nTimed out waiting for prediction")

def main():
    print("Starting Kafka Flow Test...")
    
    # Start the consumer
    print("\nStarting Kafka consumer...")
    consumer_process = start_consumer()
    
    try:
        # Wait a bit for the consumer to start
        time.sleep(5)
        
        # Test the prediction flow
        test_prediction_flow()
        
    finally:
        # Clean up
        print("\nStopping Kafka consumer...")
        consumer_process.terminate()
        consumer_process.wait()

if __name__ == "__main__":
    main() 