"""Test TheSportsDB API endpoints with premium key."""
import httpx
import json
from typing import Dict, Any
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("SPORTSDB_API_KEY")
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

async def test_endpoint(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return the response.
    
    Args:
        endpoint: API endpoint to test
        params: Query parameters
        
    Returns:
        API response data
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint}: {str(e)}")
            return {}

async def main():
    """Test main API endpoints and validate data structure."""
    # Test premium endpoints
    endpoints = {
        "lookupevent": {"id": "441613"},  # Example event ID
        "lookupeventstats": {"id": "441613"},  # Premium: Detailed stats
        "eventslast": {"id": "133604"},  # Premium: Last events for team (not limited to home)
        "lookupteam": {"id": "133604"},
        "lookupleague": {"id": "4328"},
        "lookuplineup": {"id": "441613"},  # Premium: Match lineup
        "lookuptimeline": {"id": "441613"},  # Premium: Match timeline
        "eventsnext": {"id": "133604"},  # Premium: Next 5 events
        "eventsnextleague": {"id": "4328"},  # Premium: Next 25 events in league
        "eventspastleague": {"id": "4328"},  # Premium: Last 15 events in league
        "lookup_all_teams": {"id": "4328"},  # Premium: All teams in league
        "lookup_all_players": {"id": "133604"}  # Premium: All players in team
    }
    
    results = {}
    
    for endpoint, params in endpoints.items():
        logger.info(f"\nTesting endpoint: {endpoint}")
        data = await test_endpoint(f"{endpoint}.php", params)
        results[endpoint] = data
        
        # Save raw response to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_response_{endpoint}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved response to {filename}")
        
        # Print summary of response
        if data:
            print(f"\n{endpoint} Response Summary:")
            print("-" * 50)
            
            # Handle different response structures
            if "events" in data:
                print(f"Number of events: {len(data['events'])}")
                if data["events"]:
                    print("First event keys:", list(data["events"][0].keys()))
            elif "teams" in data:
                print(f"Number of teams: {len(data['teams'])}")
                if data["teams"]:
                    print("First team keys:", list(data["teams"][0].keys()))
            elif "leagues" in data:
                print(f"Number of leagues: {len(data['leagues'])}")
                if data["leagues"]:
                    print("First league keys:", list(data["leagues"][0].keys()))
            elif "lineup" in data:
                print(f"Number of lineup entries: {len(data['lineup'])}")
                if data["lineup"]:
                    print("First lineup keys:", list(data["lineup"][0].keys()))
            elif "timeline" in data:
                print(f"Number of timeline entries: {len(data['timeline'])}")
                if data["timeline"]:
                    print("First timeline keys:", list(data["timeline"][0].keys()))
            elif "players" in data:
                print(f"Number of players: {len(data['players'])}")
                if data["players"]:
                    print("First player keys:", list(data["players"][0].keys()))
            elif "results" in data:
                print(f"Number of results: {len(data['results'])}")
                if data["results"]:
                    print("First result keys:", list(data["results"][0].keys()))
            else:
                print("Response keys:", list(data.keys()))
        else:
            print(f"No data returned for {endpoint}")
        print("-" * 50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 