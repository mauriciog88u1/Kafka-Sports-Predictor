"""Sports DB API service."""
import logging
from typing import Dict, Any, List
import httpx
from src.config import settings
from src.api.services.data_transformer import DataTransformer

logger = logging.getLogger(__name__)

BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{settings.SPORTSDB_API_KEY}"


async def get_match_data(match_id: str) -> Dict[str, Any]:
    """
    Fetch match data from TheSportsDB API and transform it into a structured format.
    
    Args:
        match_id: The ID of the match to fetch
        
    Returns:
        Dict containing match data and team statistics
    """
    try:
        # Get match details
        match_url = f"{BASE_URL}/lookupevent.php?id={match_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(match_url)
            response.raise_for_status()
            match_data = response.json()
            
            if not match_data.get("events"):
                raise ValueError(f"No match found with ID {match_id}")
                
            event = match_data["events"][0]
            
            # Get team details for both home and away teams
            home_team_url = f"{BASE_URL}/lookupteam.php?id={event['idHomeTeam']}"
            away_team_url = f"{BASE_URL}/lookupteam.php?id={event['idAwayTeam']}"
            
            home_team_response = await client.get(home_team_url)
            away_team_response = await client.get(away_team_url)
            
            home_team_response.raise_for_status()
            away_team_response.raise_for_status()
            
            home_team_data = home_team_response.json()
            away_team_data = away_team_response.json()
            
            # Get last 5 matches for both teams
            home_team_last_matches_url = f"{BASE_URL}/eventslast.php?id={event['idHomeTeam']}"
            away_team_last_matches_url = f"{BASE_URL}/eventslast.php?id={event['idAwayTeam']}"
            
            home_team_last_matches_response = await client.get(home_team_last_matches_url)
            away_team_last_matches_response = await client.get(away_team_last_matches_url)
            
            home_team_last_matches_response.raise_for_status()
            away_team_last_matches_response.raise_for_status()
            
            home_team_last_matches = home_team_last_matches_response.json()
            away_team_last_matches = away_team_last_matches_response.json()
            
            # Calculate form for both teams
            home_team_form = calculate_team_form(home_team_last_matches.get("results", []))
            away_team_form = calculate_team_form(away_team_last_matches.get("results", []))
            
            # Transform the data into our format
            transformed_data = {
                "idEvent": event["idEvent"],
                "strEvent": event["strEvent"],
                "strLeague": event["strLeague"],
                "idLeague": event.get("idLeague"),
                "strSeason": event.get("strSeason"),
                "idHomeTeam": event["idHomeTeam"],
                "strHomeTeam": event["strHomeTeam"],
                "idAwayTeam": event["idAwayTeam"],
                "strAwayTeam": event["strAwayTeam"],
                "dateEvent": event["dateEvent"],
                "strTime": event["strTime"],
                "strTimestamp": f"{event['dateEvent']}T{event['strTime']}",
                "intHomeScore": int(event["intHomeScore"]) if event.get("intHomeScore") not in (None, "") else None,
                "intAwayScore": int(event["intAwayScore"]) if event.get("intAwayScore") not in (None, "") else None,
                "strStatus": DataTransformer.map_status(event.get("strStatus")),
                "team_stats": {
                    "home": {
                        "form": home_team_form,
                        "xg_for": 1.8,  # Placeholder for expected goals
                        "xg_against": 1.2,  # Placeholder for expected goals against
                        "avg_goals_scored": 1.6,  # Placeholder for average goals scored
                        "avg_goals_conceded": 0.8,  # Placeholder for average goals conceded
                        "win_probability": 0.6  # Placeholder for win probability
                    },
                    "away": {
                        "form": away_team_form,
                        "xg_for": 1.5,  # Placeholder for expected goals
                        "xg_against": 1.4,  # Placeholder for expected goals against
                        "avg_goals_scored": 1.4,  # Placeholder for average goals scored
                        "avg_goals_conceded": 1.0,  # Placeholder for average goals conceded
                        "win_probability": 0.4  # Placeholder for win probability
                    }
                },
                "odds": {
                    "home_win": 2.0,  # Placeholder for home win odds
                    "draw": 3.5,  # Placeholder for draw odds
                    "away_win": 4.0,  # Placeholder for away win odds
                    "over_2_5": 1.8,  # Placeholder for over 2.5 goals odds
                    "under_2_5": 2.0,  # Placeholder for under 2.5 goals odds
                    "btts_yes": 1.9,  # Placeholder for both teams to score odds
                    "btts_no": 1.9  # Placeholder for both teams not to score odds
                }
            }
            
            return transformed_data
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching match data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching match data: {str(e)}")
        raise


def calculate_team_form(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate team form based on last 5 matches.
    
    Args:
        matches: List of match data
        
    Returns:
        Dict containing form statistics
    """
    if not matches:
        return {
            "last_5": [],
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_scored": 0,
            "goals_conceded": 0,
            "clean_sheets": 0,
            "failed_to_score": 0,
            "form_score": 0.0
        }
    
    form = {
        "last_5": [],
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_scored": 0,
        "goals_conceded": 0,
        "clean_sheets": 0,
        "failed_to_score": 0
    }
    
    for match in matches[:5]:
        home_score = int(match.get("intHomeScore", 0) or 0)
        away_score = int(match.get("intAwayScore", 0) or 0)
        
        if match.get("strHomeTeam") == match.get("strTeam"):
            # Team is home
            form["goals_scored"] += home_score
            form["goals_conceded"] += away_score
            
            if home_score > away_score:
                form["wins"] += 1
                form["last_5"].append("W")
            elif home_score == away_score:
                form["draws"] += 1
                form["last_5"].append("D")
            else:
                form["losses"] += 1
                form["last_5"].append("L")
                
            # Check for clean sheet
            if away_score == 0:
                form["clean_sheets"] += 1
            # Check for failed to score
            if home_score == 0:
                form["failed_to_score"] += 1
        else:
            # Team is away
            form["goals_scored"] += away_score
            form["goals_conceded"] += home_score
            
            if away_score > home_score:
                form["wins"] += 1
                form["last_5"].append("W")
            elif away_score == home_score:
                form["draws"] += 1
                form["last_5"].append("D")
            else:
                form["losses"] += 1
                form["last_5"].append("L")
                
            # Check for clean sheet
            if home_score == 0:
                form["clean_sheets"] += 1
            # Check for failed to score
            if away_score == 0:
                form["failed_to_score"] += 1
    
    # Calculate form score based on performance metrics
    # Each win is worth 3 points, draw 1 point
    points = form["wins"] * 3 + form["draws"]
    max_points = len(form["last_5"]) * 3  # Maximum possible points from matches played
    
    # Calculate goal difference impact
    goal_diff = form["goals_scored"] - form["goals_conceded"]
    
    # Calculate form score components
    match_points = (points / max_points) * 50 if max_points > 0 else 0  # 50% weight on match results
    goal_impact = min(max(goal_diff, -5), 5) * 5  # 25% weight on goal difference (-25 to +25)
    clean_sheet_bonus = (form["clean_sheets"] / len(form["last_5"])) * 15 if form["last_5"] else 0  # 15% weight on clean sheets
    scoring_penalty = (form["failed_to_score"] / len(form["last_5"])) * -10 if form["last_5"] else 0  # 10% penalty on failing to score
    
    # Calculate total form score (0-100 scale)
    form_score = match_points + goal_impact + clean_sheet_bonus + scoring_penalty
    form_score = min(max(form_score, 0), 100)  # Clamp between 0 and 100
    
    form["form_score"] = round(form_score, 1)
    return form


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
                is_home = event.get("idHomeTeam") == team_id
                if is_home:
                    goals_scored += int(event.get("intHomeScore", 0) or 0)
                    goals_conceded += int(event.get("intAwayScore", 0) or 0)
                else:
                    goals_scored += int(event.get("intAwayScore", 0) or 0)
                    goals_conceded += int(event.get("intHomeScore", 0) or 0)
                
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