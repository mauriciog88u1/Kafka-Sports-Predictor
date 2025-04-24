import hashlib
import json
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from confluent_kafka import Producer
from typing import List, Optional, Dict, Any

app = FastAPI()

# API Configuration
API_KEY = "638861"
BASE_URL = "https://www.thesportsdb.com/api/v1/json"

# Get CORS origins from environment variable
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://mauric10.com").split(",")

# Allow your frontend to talk to this backend
print("Allowed CORS origins: and allowed credentials is set to true", cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)

# Kafka producer configuration
producer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": os.getenv("KAFKA_USERNAME"),
    "sasl.password": os.getenv("KAFKA_PASSWORD"),
}
producer = Producer(producer_config)

# Temporary in-memory store for match predictions
predictions = {}


# Match schema
class Match(BaseModel):
    idEvent: str
    strEvent: str
    dateEvent: str
    strTime: str
    strVenue: Optional[str] = None
    strHomeTeam: str
    strAwayTeam: str
    idHomeTeam: Optional[str] = None
    idAwayTeam: Optional[str] = None
    intRound: Optional[str] = None
    strLeague: Optional[str] = None
    strSeason: Optional[str] = None
    playerStats: List[Dict[str, Any]] = []
    matchHistory: List[Dict[str, Any]] = []
    eventStats: Optional[Dict[str, Any]] = None
    eventLineup: Optional[Dict[str, Any]] = None
    leagueTable: List[Dict[str, Any]] = []


class MatchResponse(BaseModel):
    matches: List[Match]


class PredictionResponse(BaseModel):
    status: str
    correlation_id: str
    match: Match


class PredictionResult(BaseModel):
    match_id: str
    prediction: str


def fetch_with_error_handling(url: str) -> Dict[str, Any]:
    """Helper function to fetch data with proper error handling"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check for Patreon-only content
        if isinstance(data, str) and "Patreon Only" in data:
            return {}

        return data
    except requests.RequestException as e:
        print(f"Error fetching {url}: {str(e)}")
        return {}


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.get("/leagues")
def get_leagues():
    """Get all available leagues"""
    try:
        url = f"{BASE_URL}/{API_KEY}/all_leagues.php"
        data = fetch_with_error_handling(url)
        return data.get("leagues", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/matches", response_model=MatchResponse)
def get_matches(team_id: str = "133602"):
    try:
        # Fetch matches
        url = f"{BASE_URL}/{API_KEY}/eventsnext.php?id={team_id}"
        data = fetch_with_error_handling(url)
        matches = data.get("events", [])

        for match in matches:
            home_id = match.get("idHomeTeam")
            away_id = match.get("idAwayTeam")
            event_id = match.get("idEvent")
            match["playerStats"] = []
            match["matchHistory"] = []
            match["eventStats"] = {}
            match["eventLineup"] = {}
            match["leagueTable"] = []

            # Fetch player stats
            if home_id:
                players_url = f"{BASE_URL}/{API_KEY}/lookup_all_players.php?id={home_id}"
                players_data = fetch_with_error_handling(players_url)
                match["playerStats"].extend(players_data.get("player", []))

            if away_id:
                players_url = f"{BASE_URL}/{API_KEY}/lookup_all_players.php?id={away_id}"
                players_data = fetch_with_error_handling(players_url)
                match["playerStats"].extend(players_data.get("player", []))

            # Fetch match history
            if home_id:
                history_url = f"{BASE_URL}/{API_KEY}/eventslast.php?id={home_id}"
                history_data = fetch_with_error_handling(history_url)
                match["matchHistory"].extend(history_data.get("results", []))

            # Fetch event stats and lineup
            if event_id:
                stats_url = f"{BASE_URL}/{API_KEY}/lookupeventstats.php?id={event_id}"
                stats_data = fetch_with_error_handling(stats_url)
                match["eventStats"] = stats_data.get("eventstats", {})

                lineup_url = f"{BASE_URL}/{API_KEY}/lookuplineup.php?id={event_id}"
                lineup_data = fetch_with_error_handling(lineup_url)
                match["eventLineup"] = lineup_data

            # Fetch league table
            league_id = match.get("idLeague")
            season = match.get("strSeason")
            if league_id and season:
                table_url = f"{BASE_URL}/{API_KEY}/lookuptable.php?l={league_id}&s={season}"
                table_data = fetch_with_error_handling(table_url)
                match["leagueTable"] = table_data.get("table", [])

        return {"matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/predict", response_model=PredictionResponse)
def predict_outcome(match: Match):
    try:
        match_data = match.dict()
        # Compute a deterministic hash from idEvent using MD5
        match_hash = hashlib.md5(match_data["idEvent"].encode("utf-8")).hexdigest()
        match_data["match_id"] = match_hash

        predictions[match_hash] = "waiting for prediction..."
        try:
            producer.produce("match_updates", json.dumps(match_data).encode("utf-8"))
            producer.flush()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error producing message to Kafka: {str(e)}")
        return {"status": "sent", "match": match_data, "correlation_id": match_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/prediction/{match_id}", response_model=PredictionResult)
def get_prediction(match_id: str):
    if match_id not in predictions:
        raise HTTPException(status_code=404, detail="Match ID not found")
    return {"match_id": match_id, "prediction": predictions[match_id]}


@app.put("/prediction/{match_id}", response_model=PredictionResult)
def set_prediction(match_id: str, prediction: dict):
    if match_id not in predictions:
        raise HTTPException(status_code=404, detail="Match ID not found")
    predictions[match_id] = prediction.get("prediction", "no prediction provided")
    return {"match_id": match_id, "prediction": predictions[match_id]}
