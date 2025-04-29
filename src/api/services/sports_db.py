"""Sports DB API service."""
import logging
from typing import Dict, Any
import httpx
from src.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3"


async def get_match_data(match_id: str) -> Dict[str, Any]:
    """Get match data from Sports DB API.
    
    Args:
        match_id: The ID of the match to fetch
        
    Returns:
        Dictionary containing match data
        
    Raises:
        ValueError: If match is not found or API error occurs
    """
    async with httpx.AsyncClient() as client:
        try:
            # Get event details
            event_response = await client.get(
                f"{BASE_URL}/lookupevent.php",
                params={"id": match_id}
            )
            event_response.raise_for_status()
            event_data = event_response.json()
            
            if not event_data.get("events"):
                raise ValueError(f"Match {match_id} not found")
            
            event = event_data["events"][0]
            
            # Get event statistics if available
            stats_response = await client.get(
                f"{BASE_URL}/lookupeventstats.php",
                params={"id": match_id}
            )
            stats_data = stats_response.json() if stats_response.status_code == 200 else {}
            
            # Transform data into our schema
            transformed_data = {
                "idEvent": str(event["idEvent"]),
                "strEvent": event["strEvent"],
                "strLeague": event["strLeague"],
                "strHomeTeam": event["strHomeTeam"],
                "strAwayTeam": event["strAwayTeam"],
                "dateEvent": event["dateEvent"],
                "strTime": event["strTime"],
                "intHomeScore": int(event["intHomeScore"]) if event.get("intHomeScore") else None,
                "intAwayScore": int(event["intAwayScore"]) if event.get("intAwayScore") else None,
                "strStatus": event.get("strStatus", "Not Started"),
                "team_stats": {
                    "home": await get_team_stats(event["idHomeTeam"]),
                    "away": await get_team_stats(event["idAwayTeam"])
                }
            }
            
            # Calculate basic odds based on team stats (since we don't have real odds)
            transformed_data["odds"] = calculate_basic_odds(transformed_data["team_stats"])
            
            logger.info(f"Successfully fetched and transformed data for match {match_id}")
            return transformed_data
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching match {match_id}: {str(e)}")
            raise ValueError(f"Failed to fetch match data: {str(e)}")


async def get_team_stats(team_id: str) -> Dict[str, Any]:
    """Get team statistics from recent matches.
    
    Args:
        team_id: The ID of the team
        
    Returns:
        Dictionary containing team statistics
    """
    async with httpx.AsyncClient() as client:
        try:
            # Get last 5 events for the team
            response = await client.get(
                f"{BASE_URL}/eventslast.php",
                params={"id": team_id}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                return get_default_stats()
            
            events = data["results"]
            
            # Calculate stats from last 5 matches
            goals_scored = 0
            goals_conceded = 0
            shots_total = 0
            
            for event in events:
                is_home = event["strHomeTeam"] == event["strTeam"]
                if is_home:
                    goals_scored += int(event["intHomeScore"] or 0)
                    goals_conceded += int(event["intAwayScore"] or 0)
                else:
                    goals_scored += int(event["intAwayScore"] or 0)
                    goals_conceded += int(event["intHomeScore"] or 0)
                
                # Estimate shots based on goals (since we don't have real shot data)
                shots_total += goals_scored * 3
            
            return {
                "goals_scored_last_5": goals_scored,
                "goals_conceded_last_5": goals_conceded,
                "shots_on_target_avg": round(shots_total / len(events), 2),
                "possession_avg": 50.0  # Default since we don't have real possession data
            }
            
        except Exception as e:
            logger.warning(f"Error fetching team stats for {team_id}: {str(e)}")
            return get_default_stats()


def get_default_stats() -> Dict[str, Any]:
    """Get default team statistics when data is unavailable."""
    return {
        "goals_scored_last_5": 0,
        "goals_conceded_last_5": 0,
        "shots_on_target_avg": 0.0,
        "possession_avg": 50.0
    }


def calculate_basic_odds(team_stats: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """Calculate basic odds based on team statistics.
    
    This is a simple calculation just for demonstration. In reality,
    odds would come from a more sophisticated model or external source.
    """
    home_strength = (
        team_stats["home"]["goals_scored_last_5"] * 0.4 +
        team_stats["home"]["shots_on_target_avg"] * 0.3
    )
    away_strength = (
        team_stats["away"]["goals_scored_last_5"] * 0.4 +
        team_stats["away"]["shots_on_target_avg"] * 0.3
    )
    
    total_strength = home_strength + away_strength + 1  # Add 1 to avoid division by zero
    
    # Convert strengths to probabilities
    home_prob = home_strength / total_strength
    away_prob = away_strength / total_strength
    draw_prob = 1 - (home_prob + away_prob)
    
    # Convert probabilities to odds (with a small margin)
    margin = 1.1
    return {
        "home": round(1 / (home_prob / margin), 2),
        "draw": round(1 / (draw_prob / margin), 2),
        "away": round(1 / (away_prob / margin), 2)
    } 