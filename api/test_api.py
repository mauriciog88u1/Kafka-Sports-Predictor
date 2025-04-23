import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:8000"
MAX_RETRIES = 5
RETRY_DELAY = 2

def wait_for_server():
    """Wait for the server to be ready"""
    for i in range(MAX_RETRIES):
        try:
            response = requests.get(f"{BASE_URL}/healthz")
            if response.status_code == 200:
                print("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server to be ready... (attempt {i + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    return False

def test_health():
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/healthz")
    print(f"Status Code: {response.status_code}")
    print("Response:", response.json())

def test_leagues():
    print("\n=== Testing Leagues Endpoint ===")
    response = requests.get(f"{BASE_URL}/leagues")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\nSample League Data (first 2 leagues):")
        pprint(data[:2] if data else [])

def test_matches():
    print("\n=== Testing Matches Endpoint ===")
    response = requests.get(f"{BASE_URL}/matches", params={"team_id": "133602"})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\nSample Match Data (first match):")
        if data.get("matches"):
            pprint(data["matches"][0])
            return data["matches"][0]  # Return the first match for prediction testing
    return None

def test_prediction_flow(match):
    if not match:
        print("No match data available for prediction testing")
        return

    print("\n=== Testing Prediction Flow ===")
    
    # 1. Send prediction request
    print("\nSending prediction request...")
    predict_response = requests.post(f"{BASE_URL}/predict", json=match)
    print(f"Status Code: {predict_response.status_code}")
    if predict_response.status_code == 200:
        predict_data = predict_response.json()
        print("Prediction Response:")
        pprint(predict_data)
        
        # 2. Get prediction result
        match_id = predict_data["correlation_id"]
        print(f"\nGetting prediction for match_id: {match_id}")
        result_response = requests.get(f"{BASE_URL}/prediction/{match_id}")
        print(f"Status Code: {result_response.status_code}")
        if result_response.status_code == 200:
            print("Prediction Result:")
            pprint(result_response.json())
            
            # 3. Update prediction
            print("\nUpdating prediction...")
            update_response = requests.put(
                f"{BASE_URL}/prediction/{match_id}",
                json={"prediction": "Liverpool"}
            )
            print(f"Status Code: {update_response.status_code}")
            if update_response.status_code == 200:
                print("Updated Prediction Result:")
                pprint(update_response.json())

def main():
    print("Starting API Tests...")
    
    # Wait for server to be ready
    if not wait_for_server():
        print("Server not available after maximum retries. Exiting.")
        return
    
    # Test health endpoint
    test_health()
    
    # Test leagues endpoint
    test_leagues()
    
    # Test matches endpoint and get a match for prediction testing
    match = test_matches()
    
    # Test prediction flow with the match data
    test_prediction_flow(match)

if __name__ == "__main__":
    main() 