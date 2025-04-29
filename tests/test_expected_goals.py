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