"""Sports DB API service."""
import logging
from typing import Dict, Any, List, Tuple
import httpx
import json
import os
from datetime import datetime, timedelta
from src.config import settings
from src.api.services.data_transformer import DataTransformer
import math
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Configure logging for GCP
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{settings.SPORTSDB_API_KEY}"
CACHE_FILE = "/tmp/league_cache.json"
CACHE_EXPIRY_HOURS = 24
BATCH_SIZE = 20  # Increased batch size for faster processing
MAX_CONCURRENT_REQUESTS = 10  # Increased concurrent requests

# Global cache
cache = None
last_cache_load = None

def load_cache() -> Dict[str, Any]:
    """Load league data from cache file with in-memory caching."""
    global cache, last_cache_load
    
    # Check if in-memory cache is still valid
    if cache is not None and last_cache_load is not None:
        if (datetime.now() - last_cache_load).total_seconds() < 60:  # Refresh every minute
            return cache
    
    if not os.path.exists(CACHE_FILE):
        cache = {
            "last_updated": None,
            "matches": {},  # Direct match ID lookup
            "leagues": {}   # League data for reference
        }
        last_cache_load = datetime.now()
        return cache
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            if cache["last_updated"]:
                cache["last_updated"] = datetime.fromisoformat(cache["last_updated"])
            last_cache_load = datetime.now()
            return cache
    except Exception as e:
        logger.error(f"Error loading cache: {str(e)}")
        cache = {
            "last_updated": None,
            "matches": {},
            "leagues": {}
        }
        last_cache_load = datetime.now()
        return cache

def save_cache(cache_data: Dict[str, Any]) -> None:
    """Save league data to cache file and update in-memory cache."""
    global cache, last_cache_load
    try:
        cache_copy = cache_data.copy()
        if cache_copy["last_updated"]:
            cache_copy["last_updated"] = cache_copy["last_updated"].isoformat()
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_copy, f)
        
        # Update in-memory cache
        cache = cache_data
        last_cache_load = datetime.now()
    except Exception as e:
        logger.error(f"Error saving cache: {str(e)}")

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


async def process_match_batch(match_ids: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Process a batch of match IDs with optimized caching."""
    results = []
    errors = []
    
    # Load cache once for the entire batch
    cache = load_cache()
    
    # Split match IDs into batches
    batches = [match_ids[i:i + BATCH_SIZE] for i in range(0, len(match_ids), BATCH_SIZE)]
    
    for batch in batches:
        # Process each batch concurrently
        tasks = [process_single_match(match_id, cache) for match_id in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                errors.append({
                    "match_id": result.match_id if hasattr(result, 'match_id') else 'unknown',
                    "error": str(result)
                })
            else:
                results.append(result)
    
    return results, errors

async def process_single_match(match_id: str, cache: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single match with optimized caching."""
    try:
        # Check cache first
        if is_cache_valid(cache) and match_id in cache["matches"]:
            return cache["matches"][match_id]
        
        # If not in cache, fetch from API
        match_data, is_cached = await get_match_data(match_id, cache)
        if match_data:
            return match_data
        raise ValueError(f"No data returned for match {match_id}")
    except Exception as e:
        e.match_id = match_id
        raise

async def get_match_data(match_id: str, cache: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Fetch match data from TheSportsDB API or cache."""
    try:
        # Check cache first with direct lookup
        if is_cache_valid(cache) and match_id in cache["matches"]:
            return cache["matches"][match_id], True
        
        # If not in cache, fetch from API
        async with httpx.AsyncClient(timeout=30.0) as client:
        # Get match details
        match_url = f"{BASE_URL}/lookupevent.php?id={match_id}"
            response = await client.get(match_url)
            response.raise_for_status()
            match_data = response.json()
            
            if not match_data.get("events"):
                raise ValueError(f"No match found with ID {match_id}")
                
            event = match_data["events"][0]
            league_id = event.get("idLeague")
            
            # Get team details and last matches concurrently
            home_team_url = f"{BASE_URL}/lookupteam.php?id={event['idHomeTeam']}"
            away_team_url = f"{BASE_URL}/lookupteam.php?id={event['idAwayTeam']}"
            home_matches_url = f"{BASE_URL}/eventslast.php?id={event['idHomeTeam']}"
            away_matches_url = f"{BASE_URL}/eventslast.php?id={event['idAwayTeam']}"
            
            # Make concurrent requests with timeout
            tasks = [
                client.get(home_team_url),
                client.get(away_team_url),
                client.get(home_matches_url),
                client.get(away_matches_url)
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for errors in responses
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    raise response
                response.raise_for_status()
            
            home_team_data = responses[0].json()
            away_team_data = responses[1].json()
            home_matches = responses[2].json()
            away_matches = responses[3].json()
            
            # Calculate form and stats
            home_form = calculate_team_form(home_matches.get("results", []), event['idHomeTeam'])
            away_form = calculate_team_form(away_matches.get("results", []), event['idAwayTeam'])
            
            home_xg = calculate_expected_goals(home_form, True)
            away_xg = calculate_expected_goals(away_form, False)
            
            probabilities = calculate_win_probability(home_form, away_form)
            odds = calculate_odds(probabilities)
            
            # Transform data
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
                        "form": home_form,
                        "xg_for": home_xg,
                        "xg_against": away_xg,
                        "avg_goals_scored": round(home_form["goals_scored"] / max(1, len(home_form["last_5"])), 2),
                        "avg_goals_conceded": round(home_form["goals_conceded"] / max(1, len(home_form["last_5"])), 2),
                        "win_probability": probabilities["home"]
                    },
                    "away": {
                        "form": away_form,
                        "xg_for": away_xg,
                        "xg_against": home_xg,
                        "avg_goals_scored": round(away_form["goals_scored"] / max(1, len(away_form["last_5"])), 2),
                        "avg_goals_conceded": round(away_form["goals_conceded"] / max(1, len(away_form["last_5"])), 2),
                        "win_probability": probabilities["away"]
                    }
                },
                "odds": odds
            }
            
            # Update cache with direct match ID lookup
            cache["matches"][match_id] = transformed_data
            if league_id not in cache["leagues"]:
                cache["leagues"][league_id] = []
            cache["leagues"][league_id].append(transformed_data)
            cache["last_updated"] = datetime.now()
            save_cache(cache)
            
            return transformed_data, False
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching match data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching match data: {str(e)}")
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