"""Test Match model."""
import pytest
from datetime import datetime
from src.models.match import Match, TeamStats, MatchOdds, TeamForm
import json


@pytest.fixture
def sample_team_stats():
    """Sample team statistics fixture."""
    return TeamStats(
        form=TeamForm(
            wins=3,
            draws=2,
            losses=1,
            goals_scored=8,
            goals_conceded=4,
            clean_sheets=2,
            failed_to_score=1,
            form_score=75.0
        ),
        xg_for=1.8,
        xg_against=1.2,
        avg_goals_scored=1.6,
        avg_goals_conceded=0.8,
        win_probability=0.6
    )


@pytest.fixture
def sample_match_data(sample_team_stats):
    """Sample match data fixture."""
    return {
        "idEvent": "12345",
        "strEvent": "Arsenal vs Chelsea",
        "strLeague": "Premier League",
        "strSport": "Soccer",
        "idLeague": "4328",
        "strSeason": "2023-2024",
        "idHomeTeam": "133604",
        "idAwayTeam": "133613",
        "dateEvent": "2024-03-16",
        "strTime": "15:00:00",
        "strTimestamp": "2024-03-16T15:00:00+00:00",
        "strStatus": "Live",
        "intHomeScore": 2,
        "intAwayScore": 1,
        "strHomeTeam": "Arsenal",
        "strAwayTeam": "Chelsea",
        "strHomeTeamBadge": "https://www.thesportsdb.com/images/media/team/badge/a1af2i1557005128.png",
        "strAwayTeamBadge": "https://www.thesportsdb.com/images/media/team/badge/vwpvry1467462651.png",
        "strVenue": "Emirates Stadium",
        "strReferee": "Michael Oliver",
        "team_stats": {
            "home": sample_team_stats,
            "away": sample_team_stats
        },
        "odds": MatchOdds(
            home_win=1.8,
            draw=3.5,
            away_win=4.2,
            over_2_5=1.9,
            under_2_5=1.9,
            btts_yes=1.7,
            btts_no=2.0
        )
    }


def test_match_creation(sample_match_data):
    """Test match creation with all required fields."""
    match = Match(**sample_match_data)
    print("\nCreated Match Object:")
    print(f"Event ID: {match.idEvent}")
    print(f"Event: {match.strEvent}")
    print(f"Status: {match.strStatus}")
    print(f"Home Team: {match.strHomeTeam} ({match.intHomeScore})")
    print(f"Away Team: {match.strAwayTeam} ({match.intAwayScore})")
    assert match.idEvent == "12345"
    assert match.strEvent == "Arsenal vs Chelsea"
    assert match.strLeague == "Premier League"


def test_team_stats(sample_match_data):
    """Test team statistics structure and content."""
    match = Match(**sample_match_data)
    home_stats = match.team_stats["home"]
    away_stats = match.team_stats["away"]
    
    print("\nTeam Statistics:")
    print("Home Team Stats:")
    print(f"Form: {home_stats.form}")
    print(f"xG For: {home_stats.xg_for}")
    print(f"xG Against: {home_stats.xg_against}")
    print(f"Win Probability: {home_stats.win_probability}")
    
    assert home_stats.form.wins == 3
    assert home_stats.form.draws == 2
    assert home_stats.form.losses == 1
    assert home_stats.xg_for == 1.8
    assert home_stats.xg_against == 1.2
    assert home_stats.win_probability == 0.6
    assert home_stats == away_stats


def test_odds(sample_match_data):
    """Test match odds structure and content."""
    match = Match(**sample_match_data)
    print("\nMatch Odds:")
    print(f"Home Win: {match.odds.home_win}")
    print(f"Draw: {match.odds.draw}")
    print(f"Away Win: {match.odds.away_win}")
    print(f"Over 2.5: {match.odds.over_2_5}")
    print(f"Under 2.5: {match.odds.under_2_5}")
    print(f"BTTS Yes: {match.odds.btts_yes}")
    print(f"BTTS No: {match.odds.btts_no}")
    
    assert match.odds.home_win == 1.8
    assert match.odds.draw == 3.5
    assert match.odds.away_win == 4.2
    assert match.odds.over_2_5 == 1.9
    assert match.odds.under_2_5 == 1.9
    assert match.odds.btts_yes == 1.7
    assert match.odds.btts_no == 2.0


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


def test_form_score_calculation():
    """Test form score calculation."""
    # Create a match with test data
    form_data = TeamForm(
        wins=3,
        draws=2,
        losses=1,
        goals_scored=8,
        goals_conceded=4,
        clean_sheets=2,
        failed_to_score=1,
        form_score=0.0  # Will be calculated
    )
    
    stats = TeamStats(
        form=form_data,
        xg_for=1.8,
        xg_against=1.2,
        avg_goals_scored=1.6,
        avg_goals_conceded=0.8,
        win_probability=0.6
    )
    
    match_data = {
        "idEvent": "12345",
        "strEvent": "Test Match",
        "strLeague": "Test League",
        "strSport": "Soccer",
        "idLeague": "4328",
        "strSeason": "2023-2024",
        "idHomeTeam": "1",
        "idAwayTeam": "2",
        "strHomeTeam": "Home Team",  # Added required field
        "strAwayTeam": "Away Team",  # Added required field
        "dateEvent": "2024-03-16",
        "strTime": "15:00:00",
        "strTimestamp": "2024-03-16T15:00:00+00:00",
        "strStatus": "Not Started",
        "team_stats": {
            "home": stats,
            "away": stats
        },
        "odds": MatchOdds(
            home_win=1.8,
            draw=3.5,
            away_win=4.2,
            over_2_5=1.9,
            under_2_5=1.9,
            btts_yes=1.7,
            btts_no=2.0
        )
    }
    
    match = Match(**match_data)
    actual_score = match.calculate_form_score("home")
    
    # Calculate expected score
    wins_score = form_data.wins * 3
    draws_score = form_data.draws * 1
    goals_scored_score = form_data.goals_scored * 0.5
    clean_sheets_score = form_data.clean_sheets * 2
    goals_conceded_score = form_data.goals_conceded * -0.3
    failed_to_score_score = form_data.failed_to_score * -1
    
    total_score = (
        wins_score + draws_score + goals_scored_score +
        clean_sheets_score + goals_conceded_score + failed_to_score_score
    )
    
    # Convert to 0-100 scale
    expected_score = min(max((total_score / 25) * 100, 0), 100)
    
    print("\nForm Score Calculation:")
    print(f"Wins Score: {wins_score}")
    print(f"Draws Score: {draws_score}")
    print(f"Goals Scored Score: {goals_scored_score}")
    print(f"Clean Sheets Score: {clean_sheets_score}")
    print(f"Goals Conceded Score: {goals_conceded_score}")
    print(f"Failed to Score Score: {failed_to_score_score}")
    print(f"Total Score: {total_score}")
    print(f"Expected Score: {expected_score}")
    print(f"Actual Score: {actual_score}")
    
    assert abs(actual_score - expected_score) < 0.0001  # Allow for floating point differences


def test_match_time_parsing(sample_match_data):
    """Test match datetime parsing."""
    match = Match(**sample_match_data)
    expected_datetime = datetime(2024, 3, 16, 15, 0, 0)  # Updated to match the sample data
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