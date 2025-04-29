"""Expected goals calculation module."""
from typing import Dict, Any, List
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ExpectedGoalsCalculator:
    """Calculator for expected goals (xG) in football matches."""

    def __init__(self):
        """Initialize the xG calculator."""
        self.league_factors = {
            "Premier League": 1.0,
            "La Liga": 0.98,
            "Bundesliga": 1.02,
            "Serie A": 0.95,
            "Ligue 1": 0.93
        }
        logger.info("Initialized ExpectedGoalsCalculator")

    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data.
        
        Args:
            data: Match data dictionary
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        if "team_stats" not in data:
            raise ValueError("Missing team_stats in match data")

        for team in ["home", "away"]:
            stats = data["team_stats"].get(team, {})
            required_stats = [
                "goals_scored_last_5",
                "goals_conceded_last_5",
                "shots_on_target_avg",
                "possession_avg"
            ]
            
            for stat in required_stats:
                if stat not in stats:
                    raise ValueError(f"Missing {stat} for {team} team")
                if not isinstance(stats[stat], (int, float)):
                    raise ValueError(f"Invalid type for {stat}")
                if stats[stat] < 0:
                    raise ValueError(f"Negative value for {stat}")

    def _calculate_base_xg(self, team_stats: Dict[str, Any]) -> float:
        """Calculate base xG from team stats.
        
        Args:
            team_stats: Dictionary containing team statistics
            
        Returns:
            Base expected goals value
        """
        # Weight factors for different statistics
        weights = {
            "goals_scored_last_5": 0.3,
            "shots_on_target_avg": 0.4,
            "possession_avg": 0.3
        }
        
        # Normalize goals to per-match basis
        goals_per_match = team_stats["goals_scored_last_5"] / 5
        
        # Calculate weighted score
        weighted_score = (
            goals_per_match * weights["goals_scored_last_5"] +
            team_stats["shots_on_target_avg"] * weights["shots_on_target_avg"] * 0.2 +  # Convert shots to likely goals
            (team_stats["possession_avg"] / 100) * weights["possession_avg"]
        )
        
        return weighted_score

    def _apply_league_factor(self, xg: float, league: str) -> float:
        """Apply league-specific scoring factor.
        
        Args:
            xg: Base expected goals value
            league: League name
            
        Returns:
            Adjusted expected goals value
        """
        factor = self.league_factors.get(league, 1.0)
        return xg * factor

    def _adjust_for_historical(self, xg: float, data: Dict[str, Any], team: str) -> float:
        """Adjust xG based on historical match data if available.
        
        Args:
            xg: Current xG value
            data: Match data dictionary
            team: Team identifier ('home' or 'away')
            
        Returns:
            Adjusted expected goals value
        """
        if "historical_matches" not in data:
            return xg
            
        matches = data["historical_matches"]
        team_name = data[f"str{team.capitalize()}Team"]
        
        # Calculate average goals from historical matches
        total_goals = 0
        relevant_matches = 0
        
        for match in matches:
            if match["home_team"] == team_name:
                total_goals += match["home_goals"]
                relevant_matches += 1
            elif match["away_team"] == team_name:
                total_goals += match["away_goals"]
                relevant_matches += 1
        
        if relevant_matches > 0:
            historical_avg = total_goals / relevant_matches
            # Blend historical data with current xG (70% current, 30% historical)
            return 0.7 * xg + 0.3 * historical_avg
        
        return xg

    def calculate(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate expected goals for both teams.
        
        Args:
            data: Match data dictionary containing team stats and match information
            
        Returns:
            Dictionary with home and away expected goals
            
        Raises:
            ValueError: If input data is invalid
        """
        self._validate_input(data)
        
        result = {}
        for team in ["home", "away"]:
            # Calculate base xG
            base_xg = self._calculate_base_xg(data["team_stats"][team])
            
            # Apply league factor
            league_adjusted_xg = self._apply_league_factor(base_xg, data["strLeague"])
            
            # Adjust for historical data
            final_xg = self._adjust_for_historical(league_adjusted_xg, data, team)
            
            # Ensure result is within reasonable bounds
            result[team] = min(max(final_xg, 0), 5)
        
        logger.debug(f"Calculated xG: {result}")
        return result 