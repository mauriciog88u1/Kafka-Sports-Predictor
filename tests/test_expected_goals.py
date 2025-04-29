"""Tests for expected goals calculation."""
import pytest
from src.ml.expected_goals import ExpectedGoalsCalculator


@pytest.fixture
def calculator():
    """Create an expected goals calculator instance."""
    return ExpectedGoalsCalculator()


@pytest.fixture
def match_data():
    """Create sample match data for testing."""
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
        },
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
        }
    }


def test_calculate_expected_goals(calculator, match_data):
    """Test expected goals calculation."""
    xg = calculator.calculate(match_data)
    
    assert isinstance(xg, dict)
    assert "home" in xg
    assert "away" in xg
    assert isinstance(xg["home"], float)
    assert isinstance(xg["away"], float)
    assert 0 <= xg["home"] <= 5  # Reasonable range for xG
    assert 0 <= xg["away"] <= 5  # Reasonable range for xG


def test_calculate_with_missing_stats(calculator, match_data):
    """Test calculation with missing team stats."""
    invalid_data = match_data.copy()
    del invalid_data["team_stats"]
    
    with pytest.raises(ValueError):
        calculator.calculate(invalid_data)


def test_calculate_with_invalid_stats(calculator, match_data):
    """Test calculation with invalid team stats."""
    invalid_data = match_data.copy()
    invalid_data["team_stats"]["home"]["shots_on_target_avg"] = -1
    
    with pytest.raises(ValueError):
        calculator.calculate(invalid_data)


def test_calculate_with_different_leagues(calculator, match_data):
    """Test calculation for different leagues."""
    # Test with different league
    la_liga_data = match_data.copy()
    la_liga_data["strLeague"] = "La Liga"
    
    xg = calculator.calculate(la_liga_data)
    assert isinstance(xg, dict)
    assert "home" in xg
    assert "away" in xg


def test_calculate_with_historical_data(calculator, match_data):
    """Test calculation using historical data."""
    # Add historical data
    historical_data = match_data.copy()
    historical_data["historical_matches"] = [
        {
            "home_team": "Team A",
            "away_team": "Team C",
            "home_goals": 2,
            "away_goals": 1,
            "date": "2024-03-10"
        }
    ]
    
    xg = calculator.calculate(historical_data)
    assert isinstance(xg, dict)
    assert "home" in xg
    assert "away" in xg 