# Bet365 Match Prediction Demo

## Demo Site
Visit the live demo at [mauric10.com/bet365](https://mauric10.com/bet365)

## Project Overview
This is a demo application to predict the winner of football games. It consists of:
- A FastAPI backend deployed on Google Cloud Run  
- A React frontend for selecting teams and viewing predictions  

## What I Did
- Designed and implemented REST API endpoints (`/matches`, `/predict`, `/prediction/{id}`) in FastAPI  
- Developed a simple heuristic-based prediction algorithm with home advantage and round adjustments  
- Built a React UI with separate "Send Prediction" and "Get Prediction" actions  
- Deployed the service on Google Cloud Run with secure environment variable management  

## Website Functionality
- **League & Team Selection**: Users select a league and team to fetch upcoming matches  
- **Send Prediction**: Clicking "Send Prediction" processes the match data and returns prediction  
- **Get Prediction**: Clicking "Get Prediction" retrieves the stored prediction  
- **Result Display**: Final prediction is displayed dynamically on the page  

## Backend Flow
1. UI selects a match and clicks **Send Prediction**  
2. Frontend sends match payload (with `idEvent`) to FastAPI `POST /predict`  
3. FastAPI:  
   - Uses the `idEvent` directly as the match identifier
   - Processes the prediction immediately
   - Stores the prediction in Redis with a TTL
   - Returns the prediction result
4. UI clicks **Get Prediction**, frontend calls `GET /prediction/{idEvent}` and displays the prediction

## What I Would Do Differently Next Time
- Use a Random Forest algorithm with proper train/test splits for real machine learning  
- Implement batch prediction for entire leagues to improve efficiency
- Add authentication headers (e.g., JWT) for secure API endpoints  
- Set up GitHub–GCP integrations for CI/CD and automated deployments  
- Refactor code to follow clean code principles and improve maintainability  
- Increase test coverage with unit, integration, and end-to-end tests  
- Add JSON schema validation for all API request and response payloads  

# Bet365 API

This is a FastAPI-based backend service that provides endpoints for fetching match data and making predictions.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Copy `.env.example` to `.env` and fill in your configuration.

## Running the API

```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

### GET /matches
Fetches upcoming matches for a team.

**Query Parameters:**
- `team_id` (string, optional): Defaults to "133602"

**Response:**
```json
{
    "matches": [
        {
            "idEvent": "string",
            "strEvent": "string",
            "dateEvent": "string",
            "strTime": "string",
            "strVenue": "string",
            "strHomeTeam": "string",
            "strAwayTeam": "string",
            "idHomeTeam": "string",
            "idAwayTeam": "string",
            "intRound": "string",
            "strLeague": "string",
            "strSeason": "string",
            "playerStats": [],
            "matchHistory": [],
            "eventStats": {},
            "eventLineup": {},
            "leagueTable": []
        }
    ]
}
```

### POST /predict
Submits a match for prediction and returns the result immediately.

**Request Body:**
```json
{
    "idEvent": "string",
    "strEvent": "string",
    "dateEvent": "string",
    "strTime": "string",
    "strVenue": "string",
    "strHomeTeam": "string",
    "strAwayTeam": "string",
    "idHomeTeam": "string",
    "idAwayTeam": "string",
    "intRound": "string",
    "strLeague": "string",
    "strSeason": "string"
}
```

**Response:**
```json
{
    "idEvent": "string",
    "prediction": "string",  // Team name or "Draw"
    "timestamp": "string"    // ISO format timestamp
}
```

### GET /prediction/{idEvent}
Gets the prediction result for a match.

**Path Parameters:**
- `idEvent` (string): The event ID from the sports API

**Response:**
```json
{
    "idEvent": "string",
    "prediction": "string",  // Team name or "Draw"
    "timestamp": "string"    // ISO format timestamp
}
```

## Error Handling

The API returns standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found (prediction not found)
- 500: Internal Server Error

Error responses follow this schema:
```json
{
    "detail": "string"  // Error message
}
```

## Example Usage

### Python
```python
import requests

API_BASE = "http://localhost:8000"

# Get matches
response = requests.get(f"{API_BASE}/matches", params={"team_id": "133602"})
matches = response.json()["matches"]

# Get prediction
match = matches[0]  # First match
response = requests.post(f"{API_BASE}/predict", json=match)
prediction = response.json()
print(f"Prediction: {prediction['prediction']}")

# Get stored prediction
response = requests.get(f"{API_BASE}/prediction/{match['idEvent']}")
stored_prediction = response.json()
print(f"Stored Prediction: {stored_prediction['prediction']}")
```

### JavaScript/TypeScript
```typescript
const API_BASE = "http://localhost:8000";

// Get matches
const getMatches = async (teamId = "133602") => {
    const response = await fetch(`${API_BASE}/matches?team_id=${teamId}`);
    return response.json();
};

// Get prediction
const getPrediction = async (match) => {
    const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(match)
    });
    return response.json();
};

// Get stored prediction
const getStoredPrediction = async (idEvent) => {
    const response = await fetch(`${API_BASE}/prediction/${idEvent}`);
    return response.json();
};

// Example usage
const predictMatch = async (match) => {
    const prediction = await getPrediction(match);
    console.log("Prediction:", prediction.prediction);
    
    // Later, get stored prediction
    const stored = await getStoredPrediction(match.idEvent);
    console.log("Stored Prediction:", stored.prediction);
};
```
