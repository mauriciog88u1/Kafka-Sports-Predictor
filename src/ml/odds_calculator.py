"""Odds calculation service."""
import logging
from typing import Dict, Any, Tuple
import numpy as np
from src.models.match import Match, MatchOdds, TeamStats

logger = logging.getLogger(__name__)


class OddsCalculator:
    """Calculate match odds based on team statistics and historical data."""

    def __init__(self):
        """Initialize the odds calculator."""
        # Weights for different factors in probability calculation
        self.weights = {
            "form": 0.3,
            "goals": 0.2,
            "xg": 0.3,
            "historical": 0.2
        }
        
        # League strength factors (used to adjust probabilities)
        self.league_factors = {
            "Premier League": 1.0,
            "La Liga": 0.98,
            "Bundesliga": 1.02,
            "Serie A": 0.95,
            "Ligue 1": 0.93
        }
        
        # Margin for converting probabilities to odds
        self.margin = 1.07  # 7% margin

    def calculate_match_odds(self, match: Match) -> MatchOdds:
        """Calculate odds for a match.
        
        Args:
            match: Match object with team statistics
            
        Returns:
            MatchOdds object with calculated odds
        """
        # Calculate win probabilities
        home_prob, draw_prob, away_prob = self._calculate_match_probabilities(match)
        
        # Calculate goals probabilities
        over_prob, under_prob = self._calculate_goals_probabilities(match)
        
        # Calculate BTTS probabilities
        btts_yes_prob, btts_no_prob = self._calculate_btts_probabilities(match)
        
        # Convert probabilities to odds with margin
        return MatchOdds(
            home_win=self._probability_to_odds(home_prob),
            draw=self._probability_to_odds(draw_prob),
            away_win=self._probability_to_odds(away_prob),
            over_2_5=self._probability_to_odds(over_prob),
            under_2_5=self._probability_to_odds(under_prob),
            btts_yes=self._probability_to_odds(btts_yes_prob),
            btts_no=self._probability_to_odds(btts_no_prob)
        )

    def _calculate_match_probabilities(self, match: Match) -> Tuple[float, float, float]:
        """Calculate win/draw probabilities for the match.
        
        Args:
            match: Match object
            
        Returns:
            Tuple of (home_win_prob, draw_prob, away_win_prob)
        """
        home_stats = match.team_stats["home"]
        away_stats = match.team_stats["away"]
        
        # Calculate form-based probability
        home_form = match.calculate_form_score("home") / 100
        away_form = match.calculate_form_score("away") / 100
        
        # Calculate goals-based probability
        home_goals_ratio = home_stats.avg_goals_scored / (home_stats.avg_goals_conceded + 0.1)
        away_goals_ratio = away_stats.avg_goals_scored / (away_stats.avg_goals_conceded + 0.1)
        
        # Calculate xG-based probability
        home_xg_ratio = home_stats.xg_for / (home_stats.xg_against + 0.1)
        away_xg_ratio = away_stats.xg_for / (away_stats.xg_against + 0.1)
        
        # Combine factors with weights
        home_strength = (
            self.weights["form"] * home_form +
            self.weights["goals"] * home_goals_ratio +
            self.weights["xg"] * home_xg_ratio
        )
        
        away_strength = (
            self.weights["form"] * away_form +
            self.weights["goals"] * away_goals_ratio +
            self.weights["xg"] * away_xg_ratio
        )
        
        # Apply home advantage factor (1.1 means 10% advantage)
        home_strength *= 1.1
        
        # Calculate probabilities
        total_strength = home_strength + away_strength + 1  # Add 1 to avoid division by zero
        
        home_win_prob = home_strength / total_strength
        away_win_prob = away_strength / total_strength
        draw_prob = 1 - (home_win_prob + away_win_prob)
        
        # Apply league factor if available
        league_factor = self.league_factors.get(match.league_name, 1.0)
        home_win_prob *= league_factor
        away_win_prob *= league_factor
        
        # Normalize probabilities to sum to 1
        total = home_win_prob + draw_prob + away_win_prob
        return (
            home_win_prob / total,
            draw_prob / total,
            away_win_prob / total
        )

    def _calculate_goals_probabilities(self, match: Match) -> Tuple[float, float]:
        """Calculate over/under 2.5 goals probabilities.
        
        Args:
            match: Match object
            
        Returns:
            Tuple of (over_2.5_prob, under_2.5_prob)
        """
        home_stats = match.team_stats["home"]
        away_stats = match.team_stats["away"]
        
        # Calculate expected total goals
        expected_goals = (
            (home_stats.xg_for + away_stats.xg_for) +  # xG-based
            (home_stats.avg_goals_scored + away_stats.avg_goals_scored) +  # Historical average
            2.5  # Base expectation
        ) / 3
        
        # Calculate probability of over 2.5 using Poisson distribution
        over_prob = 1 - sum(
            np.exp(-expected_goals) * (expected_goals ** k) / np.math.factorial(k)
            for k in range(3)
        )
        
        return over_prob, 1 - over_prob

    def _calculate_btts_probabilities(self, match: Match) -> Tuple[float, float]:
        """Calculate both teams to score probabilities.
        
        Args:
            match: Match object
            
        Returns:
            Tuple of (btts_yes_prob, btts_no_prob)
        """
        home_stats = match.team_stats["home"]
        away_stats = match.team_stats["away"]
        
        # Calculate probability of each team scoring
        home_score_prob = 1 - np.exp(-(home_stats.xg_for + home_stats.avg_goals_scored) / 2)
        away_score_prob = 1 - np.exp(-(away_stats.xg_for + away_stats.avg_goals_scored) / 2)
        
        # Probability of both teams scoring
        btts_yes = home_score_prob * away_score_prob
        
        return btts_yes, 1 - btts_yes

    def _probability_to_odds(self, probability: float) -> float:
        """Convert probability to odds with margin.
        
        Args:
            probability: Raw probability
            
        Returns:
            Odds with margin
        """
        if probability <= 0:
            return 100.0  # Maximum odds
        return round(1 / (probability / self.margin), 2) 