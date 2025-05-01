"""Tests for schema validation."""
import pytest
from src.utils.validation import SchemaValidator, SchemaValidationError


@pytest.fixture
def validator():
    """Create a schema validator instance."""
    return SchemaValidator()


@pytest.fixture
def valid_match_update():
    """Create a valid match update."""
    return {
        "match": {
            "id": "12345",
            "name": "Team A vs Team B",
            "league": "Premier League",
            "league_badge": "https://example.com/badge.png",
            "home_team": "Team A",
            "away_team": "Team B",
            "date": "2024-03-20",
            "time": "20:00:00",
            "status": "Not Started",
            "home_score": None,
            "away_score": None,
            "round": 28,
            "spectators": 50000,
            "venue": "Stadium A",
            "country": "England"
        },
        "home_team": {
            "id": "133604",
            "name": "Team A",
            "badge": "https://example.com/team_a.png",
            "form": {
                "last_5": ["W", "D", "W", "L", "W"],
                "wins": 3,
                "draws": 1,
                "losses": 1,
                "goals_for": 8,
                "goals_against": 4,
                "form_rating": 2.0
            },
            "last_matches": [],
            "details": {
                "founded": 1892,
                "stadium": "Stadium A",
                "capacity": 60000,
                "location": "City A",
                "website": "https://example.com",
                "colors": {
                    "primary": "#FF0000",
                    "secondary": "#FFFFFF",
                    "tertiary": "#000000"
                }
            }
        },
        "away_team": {
            "id": "133605",
            "name": "Team B",
            "badge": "https://example.com/team_b.png",
            "form": {
                "last_5": ["L", "W", "D", "W", "L"],
                "wins": 2,
                "draws": 1,
                "losses": 2,
                "goals_for": 6,
                "goals_against": 7,
                "form_rating": 1.4
            },
            "last_matches": [],
            "details": {
                "founded": 1893,
                "stadium": "Stadium B",
                "capacity": 55000,
                "location": "City B",
                "website": "https://example.com",
                "colors": {
                    "primary": "#0000FF",
                    "secondary": "#FFFFFF",
                    "tertiary": "#000000"
                }
            }
        }
    }


@pytest.fixture
def valid_prediction_response():
    """Create a valid prediction response."""
    return {
        "match_id": "12345",
        "home_win_prob": 0.45,
        "draw_prob": 0.25,
        "away_win_prob": 0.30,
        "confidence": 0.85,
        "timestamp": "2024-03-20T15:30:00Z",
        "model_version": "1.0.0",
        "additional_info": {
            "expected_goals_home": 1.8,
            "expected_goals_away": 1.2,
            "key_factors": [
                "Home team recent form",
                "Head to head record"
            ]
        }
    }


def test_validate_match_update_success(validator, valid_match_update):
    """Test successful match update validation."""
    result = validator.validate_match_update(valid_match_update)
    assert result == valid_match_update


def test_validate_match_update_missing_required(validator):
    """Test match update validation with missing required field."""
    invalid_data = {
        "idEvent": "12345",
        # Missing strEvent
        "strLeague": "Premier League",
        "strHomeTeam": "Team A",
        "strAwayTeam": "Team B",
        "dateEvent": "2024-03-20",
        "strTime": "20:00:00",
        "strStatus": "Not Started",
        "odds": {
            "home": 2.5,
            "draw": 3.2,
            "away": 2.8
        }
    }
    
    with pytest.raises(SchemaValidationError):
        validator.validate_match_update(invalid_data)


def test_validate_match_update_invalid_status(validator, valid_match_update):
    """Test match update validation with invalid status."""
    invalid_data = valid_match_update.copy()
    invalid_data["strStatus"] = "Invalid Status"
    
    with pytest.raises(SchemaValidationError):
        validator.validate_match_update(invalid_data)


def test_validate_prediction_response_success(validator, valid_prediction_response):
    """Test successful prediction response validation."""
    result = validator.validate_prediction_response(valid_prediction_response)
    assert result == valid_prediction_response


def test_validate_prediction_response_invalid_probabilities(validator, valid_prediction_response):
    """Test prediction response validation with invalid probabilities."""
    invalid_data = valid_prediction_response.copy()
    invalid_data["home_win_prob"] = 1.5  # Should be <= 1
    
    with pytest.raises(SchemaValidationError):
        validator.validate_prediction_response(invalid_data)


def test_get_schema_errors(validator, valid_match_update):
    """Test getting detailed schema errors."""
    invalid_data = valid_match_update.copy()
    invalid_data["strStatus"] = "Invalid Status"
    
    errors = validator.get_schema_errors(invalid_data, "match_update")
    assert len(errors) > 0
    assert any(error["validator"] == "enum" for error in errors) 