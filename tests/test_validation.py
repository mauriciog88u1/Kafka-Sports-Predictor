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
        "odds": {
            "home": 2.5,
            "draw": 3.2,
            "away": 2.8
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