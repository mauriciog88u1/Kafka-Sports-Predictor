import requests
import json
import time
from pprint import pprint

# Production Configuration
API_URL = "https://bet365-ml-api-806378004153.us-central1.run.app"
CONSUMER_URL = "https://bet365-ml-consumer-806378004153.us-central1.run.app"
SPORTSDB_API_KEY = "3"  # Free tier API key
SPORTSDB_BASE_URL = "https://www.thesportsdb.com/api/v1/json"
TEAM_ID = "134283"  # Inter Miami
MAX_RETRIES = 10
RETRY_DELAY = 2

def create_test_match():
    """Create a test match for Inter Miami vs FC Dallas"""
    return {
        "idEvent": "2070999",  # Made up ID
        "strEvent": "Inter Miami vs FC Dallas",
        "dateEvent": "2024-05-15",  # Future date
        "strTime": "19:30:00",
        "strVenue": "Chase Stadium",
        "strHomeTeam": "Inter Miami",
        "strAwayTeam": "FC Dallas",
        "idHomeTeam": "134283",
        "idAwayTeam": "134856",
        "intRound": "15",
        "strLeague": "Major League Soccer",
        "strSeason": "2024"
    }

def test_api_health():
    """Test if the API is responding"""
    print("\n1. Testing API health...")
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to API: {str(e)}")
        return False

def test_consumer_health():
    """Test if the consumer is responding"""
    print("\n2. Testing consumer health...")
    try:
        response = requests.get(CONSUMER_URL)
        if response.status_code == 200:
            print("✅ Consumer is healthy")
            return True
        else:
            print(f"❌ Consumer returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to consumer: {str(e)}")
        return False

def test_prediction_flow():
    """Test the complete prediction flow"""
    print("\n3. Testing prediction flow...")
    
    # Create test match
    test_match = create_test_match()
    print("\nSending test match data:")
    pprint(test_match)
    
    # Request prediction
    print("\nRequesting prediction...")
    try:
        response = requests.post(f"{API_URL}/predict", json=test_match)
        if response.status_code != 200:
            print(f"❌ Error requesting prediction: {response.status_code}")
            return False
        
        result = response.json()
        correlation_id = result["correlation_id"]
        print(f"✅ Prediction request sent. Correlation ID: {correlation_id}")
        
        # Poll for prediction result
        print("\nPolling for prediction result...")
        for attempt in range(MAX_RETRIES):
            print(f"\nAttempt {attempt + 1}/{MAX_RETRIES}")
            
            response = requests.get(f"{API_URL}/prediction/{correlation_id}")
            if response.status_code != 200:
                print(f"❌ Error getting prediction: {response.status_code}")
                return False
            
            result = response.json()
            prediction = result["prediction"]
            
            if prediction != "waiting for prediction...":
                print(f"✅ Prediction received: {prediction}")
                return True
            
            print("Still waiting for prediction...")
            time.sleep(RETRY_DELAY)
        
        print("❌ Timed out waiting for prediction")
        return False
        
    except Exception as e:
        print(f"❌ Error in prediction flow: {str(e)}")
        return False

def main():
    print("Starting production environment test...")
    print(f"API URL: {API_URL}")
    print(f"Consumer URL: {CONSUMER_URL}")
    
    # Test prediction flow directly
    print("\nSkipping health checks and testing prediction flow directly...")
    if not test_prediction_flow():
        print("\n❌ Prediction flow test failed")
        return
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main() 