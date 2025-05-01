"""Sports DB API service."""
import logging
from typing import Dict, Any, List
import httpx
import json
import os
from datetime import datetime, timedelta
from src.config import settings
from src.api.services.data_transformer import DataTransformer
import math

# Configure logging for GCP
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{settings.SPORTSDB_API_KEY}"
CACHE_FILE = "/tmp/league_cache.json"  # Use /tmp directory which is writable in Cloud Run
CACHE_EXPIRY_HOURS = 24  # Cache expires after 24 hours

def load_cache() -> Dict[str, Any]:
    """Load league data from cache file."""
    logger.info({
        "message": "Attempting to load cache",
        "cache_file": CACHE_FILE,
        "exists": os.path.exists(CACHE_FILE)
    })
    
    if not os.path.exists(CACHE_FILE):
        logger.info({"message": "Cache file does not exist, returning empty cache"})
        return {"last_updated": None, "leagues": {}}
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            # Convert string timestamp to datetime
            if cache["last_updated"]:
                cache["last_updated"] = datetime.fromisoformat(cache["last_updated"])
                logger.info({
                    "message": "Cache loaded successfully",
                    "last_updated": cache["last_updated"].isoformat(),
                    "leagues_cached": len(cache["leagues"])
                })
            return cache
    except Exception as e:
        logger.error({
            "message": "Error loading cache",
            "error": str(e),
            "cache_file": CACHE_FILE
        })
        return {"last_updated": None, "leagues": {}}

def save_cache(cache: Dict[str, Any]) -> None:
    """Save league data to cache file."""
    try:
        # Convert datetime to string for JSON serialization
        cache_copy = cache.copy()
        if cache_copy["last_updated"]:
            cache_copy["last_updated"] = cache_copy["last_updated"].isoformat()
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_copy, f)
            logger.info({
                "message": "Cache saved successfully",
                "cache_file": CACHE_FILE,
                "leagues_cached": len(cache["leagues"])
            })
    except Exception as e:
        logger.error({
            "message": "Error saving cache",
            "error": str(e),
            "cache_file": CACHE_FILE
        })

def is_cache_valid(cache: Dict[str, Any]) -> bool:
    """Check if cache is still valid."""
    if not cache["last_updated"]:
        logger.info({"message": "Cache has no last_updated timestamp"})
        return False
    
    expiry_time = cache["last_updated"] + timedelta(hours=CACHE_EXPIRY_HOURS)
    is_valid = datetime.now() < expiry_time
    
    logger.info({
        "message": "Checking cache validity",
        "last_updated": cache["last_updated"].isoformat(),
        "expiry_time": expiry_time.isoformat(),
        "is_valid": is_valid
    })
    
    return is_valid

def calculate_team_form(matches: List[Dict[str, Any]], team_id: str) -> Dict[str, Any]:
    """Calculate team form from last 5 matches.
    
    Args:
        matches: List of match data
        team_id: ID of the team to calculate form for
        
    Returns:
        Dictionary containing form statistics
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
            "form_score": 0
        }
    
    last_5 = []
    wins = 0
    draws = 0
    losses = 0
    goals_scored = 0
    goals_conceded = 0
    clean_sheets = 0
    failed_to_score = 0
    
    for match in matches[:5]:  # Only consider last 5 matches
        is_home = match.get("idHomeTeam") == team_id
        home_score = int(match.get("intHomeScore", 0) or 0)
        away_score = int(match.get("intAwayScore", 0) or 0)
        
        if is_home:
            goals_scored += home_score
            goals_conceded += away_score
            if home_score > away_score:
                last_5.append("W")
                wins += 1
            elif home_score == away_score:
                last_5.append("D")
                draws += 1
            else:
                last_5.append("L")
                losses += 1
            if away_score == 0:
                clean_sheets += 1
            if home_score == 0:
                failed_to_score += 1
        else:
            goals_scored += away_score
            goals_conceded += home_score
            if away_score > home_score:
                last_5.append("W")
                wins += 1
            elif away_score == home_score:
                last_5.append("D")
                draws += 1
            else:
                last_5.append("L")
                losses += 1
            if home_score == 0:
                clean_sheets += 1
            if away_score == 0:
                failed_to_score += 1
    
    # Calculate form score (weighted average of recent performance)
    # Each win is worth 20 points, draw 10 points, loss 0 points
    form_score = (wins * 20 + draws * 10)
    
    # Add bonus points for goals (max 20 points)
    goal_bonus = min((goals_scored - goals_conceded) * 2, 20)
    form_score += goal_bonus
    
    # Add bonus for clean sheets (max 10 points)
    clean_sheet_bonus = min(clean_sheets * 2, 10)
    form_score += clean_sheet_bonus
    
    # Penalty for failed to score (max -10 points)
    failed_to_score_penalty = max(-failed_to_score * 2, -10)
    form_score += failed_to_score_penalty
    
    # Ensure form score is between 0 and 100
    form_score = max(0, min(100, form_score))
    
    return {
        "last_5": last_5,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "clean_sheets": clean_sheets,
        "failed_to_score": failed_to_score,
        "form_score": form_score
    }


def calculate_expected_goals(form: Dict[str, Any], is_home: bool) -> float:
    """Calculate expected goals based on team form.
    
    Args:
        form: Team form statistics
        is_home: Whether the team is playing at home
        
    Returns:
        Expected goals value
    """
    # Base xG is average goals scored in last 5 matches
    base_xg = form["goals_scored"] / max(1, len(form["last_5"]))
    
    # Adjust for form
    form_multiplier = 1.0
    if form["form_score"] > 50:
        form_multiplier = 1.2  # Good form increases xG
    elif form["form_score"] < 20:
        form_multiplier = 0.8  # Bad form decreases xG
    
    # Home advantage
    if is_home:
        form_multiplier *= 1.1  # 10% increase for home team
    
    # Adjust for clean sheets and failed to score
    if form["clean_sheets"] > 2:
        form_multiplier *= 1.1  # Good defense increases xG
    if form["failed_to_score"] > 2:
        form_multiplier *= 0.9  # Poor attack decreases xG
    
    return round(base_xg * form_multiplier, 2)


def calculate_win_probability(home_form: Dict[str, Any], away_form: Dict[str, Any]) -> Dict[str, float]:
    """Calculate win probabilities based on team form.
    
    Args:
        home_form: Home team form statistics
        away_form: Away team form statistics
        
    Returns:
        Dictionary containing win probabilities
    """
    # Base probabilities from form scores
    total_score = home_form["form_score"] + away_form["form_score"]
    if total_score == 0:
        base_home_prob = 0.4
        base_away_prob = 0.3
    else:
        base_home_prob = home_form["form_score"] / total_score
        base_away_prob = away_form["form_score"] / total_score
    
    # Add home advantage
    base_home_prob *= 1.1  # 10% increase for home team
    
    # Adjust for recent form
    if home_form["wins"] >= 3:
        base_home_prob *= 1.15  # Strong recent form
    if away_form["wins"] >= 3:
        base_away_prob *= 1.15
    
    if home_form["losses"] >= 3:
        base_home_prob *= 0.85  # Poor recent form
    if away_form["losses"] >= 3:
        base_away_prob *= 0.85
    
    # Normalize probabilities
    total_prob = base_home_prob + base_away_prob
    home_prob = base_home_prob / total_prob
    away_prob = base_away_prob / total_prob
    draw_prob = 1 - (home_prob + away_prob)
    
    # Add some uncertainty
    uncertainty = 0.1
    home_prob = (home_prob * (1 - uncertainty)) + (uncertainty / 3)
    away_prob = (away_prob * (1 - uncertainty)) + (uncertainty / 3)
    draw_prob = (draw_prob * (1 - uncertainty)) + (uncertainty / 3)
    
    # Normalize again
    total_prob = home_prob + away_prob + draw_prob
    home_prob = home_prob / total_prob
    away_prob = away_prob / total_prob
    draw_prob = draw_prob / total_prob
    
    return {
        "home": round(home_prob, 2),
        "away": round(away_prob, 2),
        "draw": round(draw_prob, 2)
    }


def calculate_odds(probabilities: Dict[str, float]) -> Dict[str, float]:
    """Calculate odds from probabilities.
    
    Args:
        probabilities: Dictionary containing win probabilities
        
    Returns:
        Dictionary containing odds
    """
    # Convert probabilities to decimal odds with 5% margin
    margin = 1.05
    return {
        "home_win": round(1 / (probabilities["home"] * margin), 2),
        "draw": round(1 / (probabilities["draw"] * margin), 2),
        "away_win": round(1 / (probabilities["away"] * margin), 2),
        "over_2_5": 1.8,  # Placeholder for now
        "under_2_5": 2.0,  # Placeholder for now
        "btts_yes": 1.9,   # Placeholder for now
        "btts_no": 1.9     # Placeholder for now
    }


async def get_match_data(match_id: str) -> Dict[str, Any]:
    """
    Fetch match data from TheSportsDB API or cache and transform it into a structured format.
    
    Args:
        match_id: The ID of the match to fetch
        
    Returns:
        Dict containing match data and team statistics
    """
    try:
        logger.info({
            "message": "Fetching match data",
            "match_id": match_id
        })
        
        # Get match details
        match_url = f"{BASE_URL}/lookupevent.php?id={match_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(match_url)
            response.raise_for_status()
            match_data = response.json()
            
            if not match_data.get("events"):
                logger.error({
                    "message": "No match found",
                    "match_id": match_id
                })
                raise ValueError(f"No match found with ID {match_id}")
                
            event = match_data["events"][0]
            league_id = event.get("idLeague")
            
            logger.info({
                "message": "Match details retrieved",
                "match_id": match_id,
                "league_id": league_id,
                "event": event["strEvent"],
                "date": event["dateEvent"]
            })
            
            # Check cache first
            cache = load_cache()
            if is_cache_valid(cache) and league_id in cache["leagues"]:
                # Check if match exists in cached league data
                for cached_match in cache["leagues"][league_id]:
                    if cached_match["idEvent"] == match_id:
                        logger.info({
                            "message": "Using cached match data",
                            "match_id": match_id,
                            "league_id": league_id,
                            "cache_hit": True
                        })
                        return cached_match
            
            logger.info({
                "message": "Cache miss - fetching fresh data",
                "match_id": match_id,
                "league_id": league_id
            })
            
            # Get team details for both home and away teams
            home_team_url = f"{BASE_URL}/lookupteam.php?id={event['idHomeTeam']}"
            away_team_url = f"{BASE_URL}/lookupteam.php?id={event['idAwayTeam']}"
            
            home_team_response = await client.get(home_team_url)
            away_team_response = await client.get(away_team_url)
            
            home_team_response.raise_for_status()
            away_team_response.raise_for_status()
            
            home_team_data = home_team_response.json()
            away_team_data = away_team_response.json()
            
            logger.info({
                "message": "Team details retrieved",
                "home_team": event["strHomeTeam"],
                "away_team": event["strAwayTeam"]
            })
            
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
            home_team_form = calculate_team_form(home_team_last_matches.get("results", []), event['idHomeTeam'])
            away_team_form = calculate_team_form(away_team_last_matches.get("results", []), event['idAwayTeam'])
            
            # Calculate expected goals
            home_xg = calculate_expected_goals(home_team_form, True)
            away_xg = calculate_expected_goals(away_team_form, False)
            
            # Calculate win probabilities
            probabilities = calculate_win_probability(home_team_form, away_team_form)
            
            # Calculate odds
            match_odds = calculate_odds(probabilities)
            
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
                        "xg_for": home_xg,
                        "xg_against": away_xg,
                        "avg_goals_scored": round(home_team_form["goals_scored"] / max(1, len(home_team_form["last_5"])), 2),
                        "avg_goals_conceded": round(home_team_form["goals_conceded"] / max(1, len(home_team_form["last_5"])), 2),
                        "win_probability": probabilities["home"]
                    },
                    "away": {
                        "form": away_team_form,
                        "xg_for": away_xg,
                        "xg_against": home_xg,
                        "avg_goals_scored": round(away_team_form["goals_scored"] / max(1, len(away_team_form["last_5"])), 2),
                        "avg_goals_conceded": round(away_team_form["goals_conceded"] / max(1, len(away_team_form["last_5"])), 2),
                        "win_probability": probabilities["away"]
                    }
                },
                "odds": match_odds
            }
            
            # Update cache
            if league_id not in cache["leagues"]:
                cache["leagues"][league_id] = []
            cache["leagues"][league_id].append(transformed_data)
            cache["last_updated"] = datetime.now()
            save_cache(cache)
            
            logger.info({
                "message": "Match data processed and cached",
                "match_id": match_id,
                "league_id": league_id,
                "home_team": event["strHomeTeam"],
                "away_team": event["strAwayTeam"],
                "predictions": {
                    "home_win_prob": probabilities["home"],
                    "draw_prob": probabilities["draw"],
                    "away_win_prob": probabilities["away"],
                    "home_xg": home_xg,
                    "away_xg": away_xg
                }
            })
            
            return transformed_data
            
    except httpx.HTTPError as e:
        logger.error({
            "message": "HTTP error fetching match data",
            "error": str(e),
            "match_id": match_id,
            "url": match_url if 'match_url' in locals() else None
        })
        raise
    except Exception as e:
        logger.error({
            "message": "Error fetching match data",
            "error": str(e),
            "match_id": match_id
        })
        raise


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