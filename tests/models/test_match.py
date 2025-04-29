"""Test Match model."""
import pytest
from datetime import datetime
from src.models.match import Match, TeamStats, MatchOdds


@pytest.fixture
def sample_team_stats():
    """Sample team statistics."""
    return TeamStats(
        form={
            "wins": 3,
            "draws": 1,
            "losses": 1,
            "goals_scored": 8,
            "goals_conceded": 4,
            "clean_sheets": 2,
            "failed_to_score": 1,
            "form_score": 75.0
        },
        xg_for=1.8,
        xg_against=1.2,
        avg_goals_scored=1.6,
        avg_goals_conceded=0.8,
        win_probability=0.6
    )


@pytest.fixture
def sample_match_data(sample_team_stats):
    """Sample match data."""
    return {
        "idEvent": "1234567",
        "strEvent": "Manchester United vs Arsenal",
        "strSport": "Soccer",
        "strLeague": "Premier League",
        "idLeague": "4328",
        "strSeason": "2023-2024",
        "idHomeTeam": "133602",
        "strHomeTeam": "Manchester United",
        "idAwayTeam": "133604",
        "strAwayTeam": "Arsenal",
        "dateEvent": "2024-03-20",
        "strTime": "15:00:00",
        "strTimestamp": "2024-03-20T15:00:00",
        "intHomeScore": 2,
        "intAwayScore": 1,
        "strStatus": "Live",
        "team_stats": {
            "home": sample_team_stats,
            "away": sample_team_stats
        },
        "odds": {
            "home_win": 2.0,
            "draw": 3.5,
            "away_win": 4.0,
            "over_2_5": 1.8,
            "under_2_5": 2.0,
            "btts_yes": 1.9,
            "btts_no": 1.9
        }
    }


def test_match_creation(sample_match_data):
    """Test match creation with valid data."""
    match = Match(**sample_match_data)
    assert match.idEvent == "1234567"
    assert match.strEvent == "Manchester United vs Arsenal"
    assert match.strLeague == "Premier League"
    assert match.idLeague == "4328"
    assert match.strSeason == "2023-2024"
    assert match.idHomeTeam == "133602"
    assert match.strHomeTeam == "Manchester United"
    assert match.idAwayTeam == "133604"
    assert match.strAwayTeam == "Arsenal"
    assert match.dateEvent == "2024-03-20"
    assert match.strTime == "15:00:00"
    assert match.strTimestamp == "2024-03-20T15:00:00"
    assert match.intHomeScore == 2
    assert match.intAwayScore == 1
    assert match.strStatus == "Live"


def test_team_stats(sample_match_data):
    """Test team statistics."""
    match = Match(**sample_match_data)
    home_stats = match.team_stats["home"]
    away_stats = match.team_stats["away"]
    
    assert home_stats.form.wins == 3
    assert home_stats.form.draws == 1
    assert home_stats.form.losses == 1
    assert home_stats.form.goals_scored == 8
    assert home_stats.form.goals_conceded == 4
    assert home_stats.form.clean_sheets == 2
    assert home_stats.form.failed_to_score == 1
    assert home_stats.form.form_score == 75.0
    assert home_stats.xg_for == 1.8
    assert home_stats.xg_against == 1.2
    assert home_stats.avg_goals_scored == 1.6
    assert home_stats.avg_goals_conceded == 0.8
    assert home_stats.win_probability == 0.6
    
    # Away stats should be identical in this test case
    assert away_stats == home_stats


def test_odds(sample_match_data):
    """Test match odds."""
    match = Match(**sample_match_data)
    odds = match.odds
    
    assert odds.home_win == 2.0
    assert odds.draw == 3.5
    assert odds.away_win == 4.0
    assert odds.over_2_5 == 1.8
    assert odds.under_2_5 == 2.0
    assert odds.btts_yes == 1.9
    assert odds.btts_no == 1.9


def test_match_status(sample_match_data):
    """Test match status methods."""
    match = Match(**sample_match_data)
    
    # Test live status
    assert match.is_live() is True
    assert match.is_finished() is False
    
    # Test finished status
    match.strStatus = "Finished"
    assert match.is_live() is False
    assert match.is_finished() is True
    
    # Test not started status
    match.strStatus = "Not Started"
    assert match.is_live() is False
    assert match.is_finished() is False


def test_form_score_calculation(sample_match_data):
    """Test form score calculation."""
    match = Match(**sample_match_data)
    home_stats = match.team_stats["home"]
    
    # Test form score calculation using the same formula as in Match.calculate_form_score
    expected_score = (
        (home_stats.form.wins * 3) +  # 3 points per win
        (home_stats.form.draws * 1) +  # 1 point per draw
        (home_stats.form.goals_scored * 0.5) +  # 0.5 points per goal scored
        (home_stats.form.clean_sheets * 2) +  # 2 points per clean sheet
        (home_stats.form.goals_conceded * -0.3) +  # -0.3 points per goal conceded
        (home_stats.form.failed_to_score * -1)  # -1 point for failing to score
    ) / 25 * 100  # Normalize to 0-100 scale
    
    # Calculate actual score
    actual_score = match.calculate_form_score("home")
    
    # Use a small tolerance for floating point arithmetic
    tolerance = 0.0001
    assert abs(actual_score - expected_score) < tolerance, f"Expected {expected_score}, got {actual_score}"


def test_match_time_parsing(sample_match_data):
    """Test match datetime parsing."""
    match = Match(**sample_match_data)
    expected_datetime = datetime(2024, 3, 20, 15, 0, 0)
    assert match.get_match_time() == expected_datetime


def test_team_stats_model():
    """Test team statistics model."""
    stats = TeamStats(
        form={
            "wins": 3,
            "draws": 1,
            "losses": 1,
            "goals_scored": 8,
            "goals_conceded": 4,
            "clean_sheets": 2,
            "failed_to_score": 1,
            "form_score": 75.0
        },
        xg_for=1.8,
        xg_against=1.2,
        avg_goals_scored=1.6,
        avg_goals_conceded=0.8,
        win_probability=0.6
    )
    assert stats.form.wins == 3
    assert stats.form.draws == 1
    assert stats.form.losses == 1
    assert stats.form.goals_scored == 8
    assert stats.form.goals_conceded == 4
    assert stats.form.clean_sheets == 2
    assert stats.form.failed_to_score == 1
    assert stats.form.form_score == 75.0
    assert stats.xg_for == 1.8
    assert stats.xg_against == 1.2
    assert stats.avg_goals_scored == 1.6
    assert stats.avg_goals_conceded == 0.8
    assert stats.win_probability == 0.6


def test_match_odds_model():
    """Test match odds model."""
    odds = MatchOdds(
        home_win=2.0,
        draw=3.5,
        away_win=4.0,
        over_2_5=1.8,
        under_2_5=2.0,
        btts_yes=1.9,
        btts_no=1.9
    )
    assert odds.home_win == 2.0
    assert odds.draw == 3.5
    assert odds.away_win == 4.0
    assert odds.over_2_5 == 1.8
    assert odds.under_2_5 == 2.0
    assert odds.btts_yes == 1.9
    assert odds.btts_no == 1.9


def test_optional_scores(sample_match_data):
    """Test match model with optional scores."""
    # Create a copy of the data to avoid modifying the fixture
    test_data = sample_match_data.copy()
    del test_data["intHomeScore"]
    del test_data["intAwayScore"]
    match = Match(**test_data)
    assert match.intHomeScore is None
    assert match.intAwayScore is None 