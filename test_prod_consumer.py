import requests
import json
import time
from datetime import datetime
from pprint import pprint

# Production URLs
API_URL = "https://bet365-ml-api-806378004153.us-central1.run.app"

def create_test_match():
    """Create a test match with current timestamp to track it easily"""
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return {
        "idEvent": f"test_{current_time}",
        "strEvent": f"Test Match {current_time}",
        "dateEvent": "2024-05-15",
        "strTime": "19:30:00",
        "strVenue": "Test Stadium",
        "strHomeTeam": "Inter Miami",
        "strAwayTeam": "FC Dallas",
        "idHomeTeam": "134283",
        "idAwayTeam": "134856",
        "intRound": "15",
        "strLeague": "Major League Soccer",
        "strSeason": "2024"
    }

def test_prediction_flow():
    """Test the complete prediction flow"""
    print("\nTesting Prediction Flow...")
    
    # Create and send test match
    test_match = create_test_match()
    print("\nSending test match:")
    pprint(test_match)
    
    try:
        # Request prediction
        print("\nRequesting prediction...")
        response = requests.post(f"{API_URL}/predict", json=test_match)
        if response.status_code != 200:
            print(f"❌ Failed to request prediction. Status: {response.status_code}")
            return False
        
        result = response.json()
        correlation_id = result.get("correlation_id")
        if not correlation_id:
            print("❌ No correlation ID received")
            return False
        
        print(f"✅ Prediction requested. Correlation ID: {correlation_id}")
        
        # Poll for prediction result
        print("\nPolling for prediction result...")
        max_attempts = 15  # Increased attempts due to batch processing
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            print(f"\nAttempt {attempt}/{max_attempts}")
            
            response = requests.get(f"{API_URL}/prediction/{correlation_id}")
            if response.status_code != 200:
                print(f"❌ Error getting prediction: {response.status_code}")
                return False
            
            result = response.json()
            prediction = result.get("prediction")
            print(f"Current status: {prediction}")
            
            if prediction and prediction != "waiting for prediction...":
                print(f"\n✅ Prediction received: {prediction}")
                return True
            
            time.sleep(4)  # Longer wait due to batch processing
        
        print("\n❌ Timed out waiting for prediction")
        return False
        
    except Exception as e:
        print(f"\n❌ Error in prediction flow: {str(e)}")
        return False

def main():
    print("Starting Consumer Test...")
    print(f"API URL: {API_URL}")
    
    # Test prediction flow
    if not test_prediction_flow():
        print("\n❌ Prediction flow test failed")
        return
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main() 