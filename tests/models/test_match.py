"""Test Match model."""
import pytest
from datetime import datetime
from src.models.match import Match, TeamStats, MatchOdds


@pytest.fixture
def sample_team_stats():
    """Sample team statistics."""
    return {
        "goals_scored_last_5": 10,
        "goals_conceded_last_5": 5,
        "shots_on_target_avg": 5.5,
        "possession_avg": 55.0
    }


@pytest.fixture
def sample_match_data(sample_team_stats):
    """Sample match data."""
    return {
        "idEvent": "1234567",
        "strEvent": "Manchester United vs Arsenal",
        "strLeague": "Premier League",
        "strHomeTeam": "Manchester United",
        "strAwayTeam": "Arsenal",
        "dateEvent": "2024-03-20",
        "strTime": "15:00:00",
        "intHomeScore": 2,
        "intAwayScore": 1,
        "strStatus": "In Play",
        "team_stats": {
            "home": sample_team_stats,
            "away": sample_team_stats
        },
        "odds": {
            "home": 2.0,
            "draw": 3.5,
            "away": 4.0
        }
    }


def test_match_model_creation(sample_match_data):
    """Test match model creation with valid data."""
    match = Match(**sample_match_data)
    assert match.id == "1234567"
    assert match.event_name == "Manchester United vs Arsenal"
    assert match.league == "Premier League"
    assert match.home_team == "Manchester United"
    assert match.away_team == "Arsenal"
    assert match.home_score == 2
    assert match.away_score == 1
    assert match.status == "In Play"


def test_team_stats_model():
    """Test team statistics model."""
    stats = TeamStats(
        goals_scored_last_5=10,
        goals_conceded_last_5=5,
        shots_on_target_avg=5.5,
        possession_avg=55.0
    )
    assert stats.goals_scored_last_5 == 10
    assert stats.goals_conceded_last_5 == 5
    assert stats.shots_on_target_avg == 5.5
    assert stats.possession_avg == 55.0


def test_match_odds_model():
    """Test match odds model."""
    odds = MatchOdds(home=2.0, draw=3.5, away=4.0)
    assert odds.home == 2.0
    assert odds.draw == 3.5
    assert odds.away == 4.0


def test_match_status_methods(sample_match_data):
    """Test match status helper methods."""
    # Test live match
    match = Match(**sample_match_data)
    assert match.is_live() is True
    assert match.is_finished() is False

    # Test finished match
    sample_match_data["strStatus"] = "FT"
    match = Match(**sample_match_data)
    assert match.is_live() is False
    assert match.is_finished() is True


def test_match_time_parsing(sample_match_data):
    """Test match datetime parsing."""
    match = Match(**sample_match_data)
    expected_datetime = datetime(2024, 3, 20, 15, 0, 0)
    assert match.get_match_time() == expected_datetime


def test_optional_scores(sample_match_data):
    """Test match model with optional scores."""
    # Create a copy of the data to avoid modifying the fixture
    test_data = sample_match_data.copy()
    del test_data["intHomeScore"]
    del test_data["intAwayScore"]
    match = Match(**test_data)
    assert match.home_score is None
    assert match.away_score is None 