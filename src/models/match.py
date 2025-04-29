"""Match model."""
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class TeamForm(BaseModel):
    """Team form model based on last 5 matches."""
    wins: int = Field(default=0, description="Number of wins in last 5 matches")
    draws: int = Field(default=0, description="Number of draws in last 5 matches")
    losses: int = Field(default=0, description="Number of losses in last 5 matches")
    goals_scored: int = Field(default=0, description="Goals scored in last 5 matches")
    goals_conceded: int = Field(default=0, description="Goals conceded in last 5 matches")
    clean_sheets: int = Field(default=0, description="Clean sheets in last 5 matches")
    failed_to_score: int = Field(default=0, description="Matches failed to score in last 5")
    form_score: float = Field(default=0.0, description="Calculated form score (0-100)")


class TeamStats(BaseModel):
    """Team statistics model."""
    form: TeamForm = Field(description="Team form based on last 5 matches")
    xg_for: float = Field(default=0.0, description="Expected goals for")
    xg_against: float = Field(default=0.0, description="Expected goals against")
    avg_goals_scored: float = Field(default=0.0, description="Average goals scored per match")
    avg_goals_conceded: float = Field(default=0.0, description="Average goals conceded per match")
    win_probability: float = Field(default=0.0, description="Calculated win probability")


class MatchOdds(BaseModel):
    """Match odds model."""
    home_win: float = Field(description="Home win probability converted to odds")
    draw: float = Field(description="Draw probability converted to odds")
    away_win: float = Field(description="Away win probability converted to odds")
    over_2_5: float = Field(description="Over 2.5 goals probability converted to odds")
    under_2_5: float = Field(description="Under 2.5 goals probability converted to odds")
    btts_yes: float = Field(description="Both teams to score - Yes probability converted to odds")
    btts_no: float = Field(description="Both teams to score - No probability converted to odds")


class MatchPrediction(BaseModel):
    """Match prediction model."""
    expected_goals_home: float = Field(description="Expected goals for home team")
    expected_goals_away: float = Field(description="Expected goals for away team")
    win_probability_home: float = Field(description="Home team win probability")
    win_probability_draw: float = Field(description="Draw probability")
    win_probability_away: float = Field(description="Away team win probability")
    confidence_score: float = Field(description="Prediction confidence score (0-100)")


class Match(BaseModel):
    """Match model."""
    # Basic match information
    idEvent: str = Field(description="Unique identifier for the match")
    idAPIfootball: Optional[str] = Field(default=None, description="API Football ID")
    strEvent: str = Field(description="Name of the match")
    strEventAlternate: Optional[str] = Field(default=None, description="Alternate match name")
    strFilename: Optional[str] = Field(default=None, description="Match filename")
    strSport: str = Field(description="Sport type")
    
    # League information
    idLeague: str = Field(description="League ID")
    strLeague: str = Field(description="League name")
    strLeagueBadge: Optional[str] = Field(default=None, description="League badge URL")
    strSeason: str = Field(description="Season")
    intRound: Optional[int] = Field(default=None, description="Round number")
    
    # Team information
    idHomeTeam: str = Field(description="Home team ID")
    strHomeTeam: str = Field(description="Home team name")
    strHomeTeamBadge: Optional[str] = Field(default=None, description="Home team badge URL")
    idAwayTeam: str = Field(description="Away team ID")
    strAwayTeam: str = Field(description="Away team name")
    strAwayTeamBadge: Optional[str] = Field(default=None, description="Away team badge URL")
    
    # Match details
    dateEvent: str = Field(description="Match date")
    strTime: str = Field(description="Match time")
    strTimestamp: str = Field(description="Match timestamp")
    intHomeScore: Optional[int] = Field(default=None, description="Home team score")
    intAwayScore: Optional[int] = Field(default=None, description="Away team score")
    intSpectators: Optional[int] = Field(default=None, description="Number of spectators")
    strOfficial: Optional[str] = Field(default=None, description="Match official")
    strStatus: Optional[str] = Field(default=None, description="Match status")
    strPostponed: Optional[str] = Field(default=None, description="Postponement status")
    strLocked: Optional[str] = Field(default=None, description="Lock status")
    
    # Venue information
    idVenue: Optional[str] = Field(default=None, description="Venue ID")
    strVenue: Optional[str] = Field(default=None, description="Venue name")
    strCountry: Optional[str] = Field(default=None, description="Country")
    strCity: Optional[str] = Field(default=None, description="City")
    
    # Our calculated fields
    team_stats: Dict[str, TeamStats] = Field(description="Team statistics")
    odds: MatchOdds = Field(description="Calculated match odds")
    prediction: Optional[MatchPrediction] = Field(default=None, description="Match prediction")

    def is_live(self) -> bool:
        """Check if match is currently live."""
        return self.strStatus and self.strStatus.lower() in ["in play", "playing", "live"]

    def is_finished(self) -> bool:
        """Check if match is finished."""
        return self.strStatus and self.strStatus.lower() in ["finished", "ft", "completed"]

    def get_match_time(self) -> datetime:
        """Get match datetime."""
        return datetime.strptime(f"{self.dateEvent} {self.strTime}", "%Y-%m-%d %H:%M:%S")

    def calculate_form_score(self, team: str) -> float:
        """Calculate form score for a team (0-100).
        
        Args:
            team: Either 'home' or 'away'
            
        Returns:
            Form score between 0 and 100
        """
        if team not in self.team_stats:
            return 0.0
            
        form = self.team_stats[team].form
        
        # Weight different factors
        win_points = form.wins * 3
        draw_points = form.draws * 1
        goals_points = form.goals_scored * 0.5
        clean_sheet_points = form.clean_sheets * 2
        conceded_penalty = form.goals_conceded * -0.3
        failed_to_score_penalty = form.failed_to_score * -1
        
        # Calculate total score (max possible = 25)
        total = win_points + draw_points + goals_points + clean_sheet_points + conceded_penalty + failed_to_score_penalty
        
        # Convert to 0-100 scale
        return min(max((total / 25) * 100, 0), 100) 