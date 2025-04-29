"""Data transformer service for TheSportsDB API responses."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from src.models.match import Match, TeamStats, MatchOdds

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transform TheSportsDB API data into our model format."""

    @staticmethod
    def map_status(status: str) -> str:
        """Map TheSportsDB status to our schema's status enum.
        
        Args:
            status: Status from TheSportsDB API
            
        Returns:
            Mapped status matching our schema's enum
        """
        status_lower = status.lower() if status else ""
        
        if status_lower in ["in play", "playing", "live"]:
            return "Live"
        elif status_lower in ["match finished", "finished", "ft", "completed"]:
            return "Finished"
        elif status_lower in ["postponed", "delayed"]:
            return "Postponed"
        elif status_lower in ["cancelled", "canceled", "abandoned"]:
            return "Cancelled"
        else:
            return "Not Started"

    @staticmethod
    def transform_event(event_data: Dict[str, Any], stats_data: Dict[str, Any] = None) -> Match:
        """Transform event data into Match model.
        
        Args:
            event_data: Raw event data from API
            stats_data: Optional event statistics data
            
        Returns:
            Match object
            
        Raises:
            ValueError: If required data is missing
        """
        if not event_data:
            raise ValueError("No event data provided")
            
        # Extract basic event data
        event = event_data.get("events", [{}])[0]
        
        # Map the status to our schema's enum
        status = DataTransformer.map_status(event.get("strStatus"))
        
        # Create team statistics
        home_stats = TeamStats(
            goals_scored_last_5=0,  # Need to fetch from historical data
            goals_conceded_last_5=0,  # Need to fetch from historical data
            shots_on_target_avg=0.0,  # Not available in free tier
            possession_avg=0.0  # Not available in free tier
        )
        
        away_stats = TeamStats(
            goals_scored_last_5=0,
            goals_conceded_last_5=0,
            shots_on_target_avg=0.0,
            possession_avg=0.0
        )
        
        # Create default odds (since not provided by API)
        odds = MatchOdds(
            home=0.0,
            draw=0.0,
            away=0.0
        )
        
        # Create Match object
        return Match(
            idEvent=event.get("idEvent", ""),
            strEvent=event.get("strEvent", ""),
            strLeague=event.get("strLeague", ""),
            strHomeTeam=event.get("strHomeTeam", ""),
            strAwayTeam=event.get("strAwayTeam", ""),
            dateEvent=event.get("dateEvent", ""),
            strTime=event.get("strTime", ""),
            intHomeScore=event.get("intHomeScore"),
            intAwayScore=event.get("intAwayScore"),
            strStatus=status,  # Use mapped status
            team_stats={
                "home": home_stats,
                "away": away_stats
            },
            odds=odds
        )

    @staticmethod
    async def enrich_team_stats(match: Match, home_last_matches: Dict[str, Any], away_last_matches: Dict[str, Any]) -> Match:
        """Enrich match with team statistics from historical matches.
        
        Args:
            match: Match object to enrich
            home_last_matches: Last matches data for home team
            away_last_matches: Last matches data for away team
            
        Returns:
            Enriched Match object
        """
        # Process home team stats
        home_stats = DataTransformer._calculate_team_stats(
            home_last_matches.get("results", []),
            match.home_team
        )
        match.team_stats["home"] = home_stats
        
        # Process away team stats
        away_stats = DataTransformer._calculate_team_stats(
            away_last_matches.get("results", []),
            match.away_team
        )
        match.team_stats["away"] = away_stats
        
        return match

    @staticmethod
    def _calculate_team_stats(last_matches: list, team_name: str) -> TeamStats:
        """Calculate team statistics from last matches.
        
        Args:
            last_matches: List of last matches
            team_name: Name of the team to calculate stats for
            
        Returns:
            TeamStats object
        """
        goals_scored = 0
        goals_conceded = 0
        matches_counted = 0
        
        for match in last_matches:
            if matches_counted >= 5:
                break
                
            if match.get("strHomeTeam") == team_name:
                home_score = int(match.get("intHomeScore", 0) or 0)
                away_score = int(match.get("intAwayScore", 0) or 0)
                goals_scored += home_score
                goals_conceded += away_score
            elif match.get("strAwayTeam") == team_name:
                home_score = int(match.get("intHomeScore", 0) or 0)
                away_score = int(match.get("intAwayScore", 0) or 0)
                goals_scored += away_score
                goals_conceded += home_score
                
            matches_counted += 1
            
        return TeamStats(
            goals_scored_last_5=goals_scored,
            goals_conceded_last_5=goals_conceded,
            shots_on_target_avg=0.0,  # Not available in free tier
            possession_avg=0.0  # Not available in free tier
        ) 