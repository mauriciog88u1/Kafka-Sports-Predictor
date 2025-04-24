import requests
import json
import time
from pprint import pprint

# Configuration
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

def get_matches():
    """Fetch upcoming matches from TheSportsDB API"""
    print("\n1. Fetching upcoming matches from TheSportsDB...")
    response = requests.get(f"{SPORTSDB_BASE_URL}/{SPORTSDB_API_KEY}/eventsnext.php", params={"id": TEAM_ID})
    if response.status_code != 200:
        print(f"Error fetching matches from TheSportsDB: {response.status_code}")
        return None
    
    matches = response.json().get("events", [])
    if not matches:
        print("No upcoming matches found in TheSportsDB")
        return None
    
    print(f"Found {len(matches)} upcoming matches")
    return matches

def find_inter_miami_match(matches):
    """Find the Inter Miami vs FC Dallas match"""
    for match in matches:
        if match['strEvent'] == "Inter Miami vs FC Dallas":
            return match
    return None

def display_matches(matches):
    """Display matches and select the first one"""
    print("\nUpcoming Matches:")
    for i, match in enumerate(matches):
        print(f"{i+1}. {match['strEvent']} on {match['dateEvent']} at {match['strTime']}")
    
    if matches:
        selected_match = matches[0]  # Just take the first match
        print(f"\nSelected match: {selected_match['strEvent']}")
        return selected_match
    else:
        print("\nError: No matches available")
        return None

def request_prediction(match):
    """Simulate UI requesting prediction"""
    print("\n2. Requesting prediction...")
    print("Sending match data:")
    pprint(match)  # Print the match data being sent
    
    response = requests.post(f"{API_URL}/predict", json=match)
    if response.status_code != 200:
        print(f"Error requesting prediction: {response.status_code}")
        return None
    
    result = response.json()
    correlation_id = result["correlation_id"]
    print(f"Prediction request sent. Correlation ID: {correlation_id}")
    return correlation_id

def check_consumer_status():
    """Check if ML consumer is running"""
    print("\n3. Checking ML consumer status...")
    try:
        response = requests.get(CONSUMER_URL)
        if response.status_code == 200:
            print("ML consumer is running")
            return True
    except:
        print("ML consumer is not responding")
        return False

def poll_prediction(correlation_id):
    """Simulate UI polling for prediction result"""
    print("\n4. Polling for prediction result...")
    
    for attempt in range(MAX_RETRIES):
        print(f"\nAttempt {attempt + 1}/{MAX_RETRIES}")
        
        response = requests.get(f"{API_URL}/prediction/{correlation_id}")
        if response.status_code != 200:
            print(f"Error getting prediction: {response.status_code}")
            return None
        
        result = response.json()
        prediction = result["prediction"]
        
        if prediction != "waiting for prediction...":
            print(f"Prediction received: {prediction}")
            return prediction
        
        print("Still waiting for prediction...")
        time.sleep(RETRY_DELAY)
    
    print("Timed out waiting for prediction")
    return None

def main():
    print("Starting end-to-end test flow...")
    
    # 1. Get matches (simulates UI loading matches)
    matches = get_matches()
    if not matches:
        return
    
    # 2. Display matches and get selection (simulates user interaction)
    selected_match = display_matches(matches)
    if not selected_match:
        return
    
    # 3. Request prediction for selected match
    correlation_id = request_prediction(selected_match)
    if not correlation_id:
        return
    
    # 4. Verify ML consumer is running
    if not check_consumer_status():
        print("Warning: ML consumer may not be processing predictions")
    
    # 5. Poll for prediction result
    final_prediction = poll_prediction(correlation_id)
    
    if final_prediction:
        print("\nTest flow completed successfully!")
        print(f"Final prediction for {selected_match['strEvent']}: {final_prediction}")
    else:
        print("\nTest flow failed to get prediction")

if __name__ == "__main__":
    main() 