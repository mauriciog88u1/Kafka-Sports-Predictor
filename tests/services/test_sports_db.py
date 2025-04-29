"""Test Sports DB API service."""
import pytest
from unittest.mock import patch, AsyncMock
from src.api.services.sports_db import (
    get_match_data,
    get_team_stats,
    get_default_stats,
    calculate_basic_odds
)


@pytest.fixture
def mock_event_response():
    """Mock event response from Sports DB API."""
    return {
        "events": [{
            "idEvent": "1234567",
            "strEvent": "Manchester United vs Arsenal",
            "strLeague": "Premier League",
            "strHomeTeam": "Manchester United",
            "strAwayTeam": "Arsenal",
            "dateEvent": "2024-03-20",
            "strTime": "15:00:00",
            "intHomeScore": "2",
            "intAwayScore": "1",
            "strStatus": "In Play",
            "idHomeTeam": "133612",
            "idAwayTeam": "133604"
        }]
    }


@pytest.fixture
def mock_team_events_response():
    """Mock team events response from Sports DB API."""
    return {
        "results": [
            {
                "strHomeTeam": "Manchester United",
                "strAwayTeam": "Liverpool",
                "strTeam": "Manchester United",
                "intHomeScore": "2",
                "intAwayScore": "1"
            },
            {
                "strHomeTeam": "Chelsea",
                "strAwayTeam": "Manchester United",
                "strTeam": "Manchester United",
                "intHomeScore": "1",
                "intAwayScore": "3"
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_match_data(mock_event_response, mock_team_events_response):
    """Test getting match data."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        # Mock event response
        mock_instance.get.side_effect = [
            AsyncMock(
                status_code=200,
                json=lambda: mock_event_response,
                raise_for_status=lambda: None
            ),
            AsyncMock(
                status_code=200,
                json=lambda: {},
                raise_for_status=lambda: None
            ),
            # Mock team stats responses
            AsyncMock(
                status_code=200,
                json=lambda: mock_team_events_response,
                raise_for_status=lambda: None
            ),
            AsyncMock(
                status_code=200,
                json=lambda: mock_team_events_response,
                raise_for_status=lambda: None
            )
        ]

        result = await get_match_data("1234567")

        assert result["idEvent"] == "1234567"
        assert result["strEvent"] == "Manchester United vs Arsenal"
        assert "team_stats" in result
        assert "odds" in result
        assert isinstance(result["team_stats"], dict)
        assert isinstance(result["odds"], dict)


@pytest.mark.asyncio
async def test_get_team_stats(mock_team_events_response):
    """Test getting team statistics."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        mock_instance.get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_team_events_response,
            raise_for_status=lambda: None
        )

        stats = await get_team_stats("133612")
        
        assert isinstance(stats["goals_scored_last_5"], int)
        assert isinstance(stats["goals_conceded_last_5"], int)
        assert isinstance(stats["shots_on_target_avg"], float)
        assert isinstance(stats["possession_avg"], float)


def test_get_default_stats():
    """Test getting default statistics."""
    stats = get_default_stats()
    assert stats["goals_scored_last_5"] == 0
    assert stats["goals_conceded_last_5"] == 0
    assert stats["shots_on_target_avg"] == 0.0
    assert stats["possession_avg"] == 50.0


def test_calculate_basic_odds():
    """Test calculating basic odds."""
    team_stats = {
        "home": {
            "goals_scored_last_5": 10,
            "goals_conceded_last_5": 5,
            "shots_on_target_avg": 5.5,
            "possession_avg": 55.0
        },
        "away": {
            "goals_scored_last_5": 8,
            "goals_conceded_last_5": 7,
            "shots_on_target_avg": 4.5,
            "possession_avg": 45.0
        }
    }
    
    odds = calculate_basic_odds(team_stats)
    assert isinstance(odds["home"], float)
    assert isinstance(odds["draw"], float)
    assert isinstance(odds["away"], float)
    assert odds["home"] > 1.0
    assert odds["draw"] > 1.0
    assert odds["away"] > 1.0


@pytest.mark.asyncio
async def test_get_match_data_not_found():
    """Test getting match data for non-existent match."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        mock_instance.get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"events": None},
            raise_for_status=lambda: None
        )

        with pytest.raises(ValueError, match="Match .* not found"):
            await get_match_data("999999") 