"""Tests for the API endpoints."""
import json
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.utils.validation import SchemaValidator


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_sports_db_response():
    """Create a mock response from sports DB API."""
    return {
        "idEvent": "12345",
        "strEvent": "Team A vs Team B",
        "strLeague": "Premier League",
        "strHomeTeam": "Team A",
        "strAwayTeam": "Team B",
        "dateEvent": "2024-03-20",
        "strTime": "20:00:00",
        "intHomeScore": None,
        "intAwayScore": None,
        "strStatus": "Not Started",
        "team_stats": {
            "home": {
                "goals_scored_last_5": 8,
                "goals_conceded_last_5": 4,
                "shots_on_target_avg": 5.2,
                "possession_avg": 55.5
            },
            "away": {
                "goals_scored_last_5": 6,
                "goals_conceded_last_5": 5,
                "shots_on_target_avg": 4.8,
                "possession_avg": 48.5
            }
        },
        "odds": {
            "home": 2.5,
            "draw": 3.2,
            "away": 2.8
        }
    }


def test_process_batch_success(test_client, mock_sports_db_response):
    """Test successful batch processing of match IDs."""
    match_ids = ["12345", "67890"]
    
    with patch('src.api.services.sports_db.get_match_data', new_callable=AsyncMock) as mock_get_match, \
         patch('src.api.services.kafka.produce_message', new_callable=AsyncMock) as mock_kafka:
        
        # Set up mocks
        mock_get_match.return_value = mock_sports_db_response
        
        # Make request
        response = test_client.post(
            "/api/v1/matches/batch",
            json={"match_ids": match_ids}
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["processed"] == 2
        
        # Verify calls
        assert mock_get_match.call_count == 2
        assert mock_kafka.call_count == 2


def test_process_batch_empty(test_client):
    """Test batch processing with empty match IDs list."""
    response = test_client.post(
        "/api/v1/matches/batch",
        json={"match_ids": []}
    )
    
    assert response.status_code == 422
    assert "detail" in response.json()


def test_process_batch_invalid_id(test_client, mock_sports_db_response):
    """Test batch processing with an invalid match ID."""
    with patch('src.api.services.sports_db.get_match_data', new_callable=AsyncMock) as mock_get_match:
        mock_get_match.side_effect = ValueError("Match not found")
        
        response = test_client.post(
            "/api/v1/matches/batch",
            json={"match_ids": ["invalid_id"]}
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "error" in response.json()["detail"]


def test_process_batch_duplicate_ids(test_client, mock_sports_db_response):
    """Test batch processing with duplicate match IDs."""
    match_ids = ["12345", "12345"]  # Duplicate ID
    
    with patch('src.api.services.sports_db.get_match_data', new_callable=AsyncMock) as mock_get_match:
        mock_get_match.return_value = mock_sports_db_response
        
        response = test_client.post(
            "/api/v1/matches/batch",
            json={"match_ids": match_ids}
        )
        
        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()


def test_process_batch_validation_error(test_client, mock_sports_db_response):
    """Test batch processing with invalid match data."""
    with patch('src.api.services.sports_db.get_match_data', new_callable=AsyncMock) as mock_get_match:
        # Return invalid data (missing required fields)
        mock_get_match.return_value = {"event_name": "Invalid Match"}
        
        response = test_client.post(
            "/api/v1/matches/batch",
            json={"match_ids": ["12345"]}
        )
        
        assert response.status_code == 404
        assert "error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_predictions(test_client):
    """Test getting predictions for a match."""
    match_id = "12345"
    prediction_data = {
        "match_id": match_id,
        "home_win_prob": 0.45,
        "draw_prob": 0.25,
        "away_win_prob": 0.30,
        "timestamp": "2024-03-20T15:30:00Z"
    }
    
    with patch('src.api.services.predictions.get_prediction_from_db', new_callable=AsyncMock) as mock_get_pred:
        mock_get_pred.return_value = prediction_data
        
        response = test_client.get(f"/api/v1/predictions/{match_id}")
        
        assert response.status_code == 200
        assert response.json() == prediction_data


@pytest.mark.asyncio
async def test_get_predictions_not_found(test_client):
    """Test getting predictions for a non-existent match."""
    with patch('src.api.services.predictions.get_prediction_from_db', new_callable=AsyncMock) as mock_get_pred:
        mock_get_pred.return_value = None
        
        response = test_client.get("/api/v1/predictions/nonexistent")
        
        assert response.status_code == 404
        assert "no prediction found" in response.json()["detail"].lower() 