from typing import Optional, List
from fastapi import FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from confluent_kafka import Producer
import os
import json
import uuid

app = FastAPI()

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to restrict this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kafka producer config
producer_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP"),
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": os.getenv("KAFKA_USERNAME"),
    "sasl.password": os.getenv("KAFKA_PASSWORD"),
}
producer = Producer(producer_config)

# Temporary storage for match predictions
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
    playerStats: Optional[List[dict]] = []
    matchHistory: Optional[List[dict]] = []
    eventStats: Optional[dict] = None
    eventLineup: Optional[dict] = None
    leagueTable: Optional[List[dict]] = []


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.get("/matches")
def get_matches(team_id: str = "133602"):
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={team_id}"
    response = requests.get(url)
    matches = response.json().get("events", [])

    for match in matches:
        home_id = match.get("idHomeTeam")
        away_id = match.get("idAwayTeam")
        event_id = match.get("idEvent")
        match["playerStats"] = []
        match["matchHistory"] = []
        match["eventStats"] = {}
        match["eventLineup"] = {}
        match["leagueTable"] = []

        if home_id:
            players_url = f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={home_id}"
            players_resp = requests.get(players_url)
            match["playerStats"].extend(players_resp.json().get("player", []))

        if away_id:
            players_url = f"https://www.thesportsdb.com/api/v1/json/3/lookup_all_players.php?id={away_id}"
            players_resp = requests.get(players_url)
            match["playerStats"].extend(players_resp.json().get("player", []))

        if home_id:
            history_url = f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={home_id}"
            history_resp = requests.get(history_url)
            match["matchHistory"].extend(history_resp.json().get("results", []))

        if event_id:
            stats_url = f"https://www.thesportsdb.com/api/v1/json/3/lookupeventstats.php?id={event_id}"
            stats_resp = requests.get(stats_url)
            match["eventStats"] = stats_resp.json().get("eventstats", {})

            lineup_url = f"https://www.thesportsdb.com/api/v1/json/3/lookuplineup.php?id={event_id}"
            lineup_resp = requests.get(lineup_url)
            match["eventLineup"] = lineup_resp.json()

        league_id = match.get("idLeague")
        season = match.get("strSeason")
        if league_id and season:
            table_url = f"https://www.thesportsdb.com/api/v1/json/3/lookuptable.php?l={league_id}&s={season}"
            table_resp = requests.get(table_url)
            match["leagueTable"] = table_resp.json().get("table", [])

    return {"matches": matches}


@app.post("/predict")
def predict_outcome(match: Match):
    # Generate a unique ID for each match to correlate with prediction
    match_id = str(uuid.uuid4())

    match_data = match.dict()
    match_data["match_id"] = match_id

    # Set initial status to 'waiting for prediction...'
    predictions[match_id] = "waiting for prediction..."

    # Send match data to Kafka
    producer.produce("match_updates", json.dumps(match_data).encode("utf-8"))
    producer.flush()

    return {"status": "sent", "match": match_data, "correlation_id": match_id}


@app.get("/prediction/{match_id}")
def get_prediction(match_id: str):
    # If prediction is not ready, show waiting message
    prediction = predictions.get(match_id, "waiting for prediction...")
    return {"match_id": match_id, "prediction": prediction}

@app.put("/prediction/{match_id}")
def set_prediction(match_id: str, prediction: dict):
    # Update the prediction status for this match ID
    predictions[match_id] = prediction["prediction"]
    return {"status": "prediction updated", "match_id": match_id, "prediction": prediction["prediction"]}
