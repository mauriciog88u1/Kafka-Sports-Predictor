import hashlib
import json
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from confluent_kafka import Producer

app = FastAPI()

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider restricting this in production
    allow_methods=["*"],
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
    strVenue: str = None
    strHomeTeam: str
    strAwayTeam: str
    idHomeTeam: str = None
    idAwayTeam: str = None
    intRound: str = None
    strLeague: str = None
    strSeason: str = None
    playerStats: list = []
    matchHistory: list = []
    eventStats: dict = None
    eventLineup: dict = None
    leagueTable: list = []

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
    match_data = match.dict()
    # Compute a deterministic hash from idEvent using MD5
    match_hash = hashlib.md5(match_data["idEvent"].encode("utf-8")).hexdigest()
    match_data["match_id"] = match_hash

    predictions[match_hash] = "waiting for prediction..."
    try:
        producer.produce("match_updates", json.dumps(match_data).encode("utf-8"))
        producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error producing message to Kafka")
    return {"status": "sent", "match": match_data, "correlation_id": match_hash}

@app.get("/prediction/{match_id}")
def get_prediction(match_id: str):
    prediction = predictions.get(match_id, "waiting for prediction...")
    return {"match_id": match_id, "prediction": prediction}

@app.put("/prediction/{match_id}")
def set_prediction(match_id: str, prediction: dict):
    predictions[match_id] = prediction.get("prediction", "no prediction provided")
    return {"status": "prediction updated", "match_id": match_id, "prediction": predictions[match_id]}
