"""Match model."""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TeamStats(BaseModel):
    """Team statistics model."""
    goals_scored_last_5: int = Field(description="Goals scored in last 5 matches")
    goals_conceded_last_5: int = Field(description="Goals conceded in last 5 matches")
    shots_on_target_avg: float = Field(description="Average shots on target per match")
    possession_avg: float = Field(description="Average possession percentage")


class MatchOdds(BaseModel):
    """Match odds model."""
    home: float = Field(description="Home win odds")
    draw: float = Field(description="Draw odds")
    away: float = Field(description="Away win odds")


class Match(BaseModel):
    """Match model."""
    id: str = Field(alias="idEvent", description="Match ID")
    event_name: str = Field(alias="strEvent", description="Event name")
    league: str = Field(alias="strLeague", description="League name")
    home_team: str = Field(alias="strHomeTeam", description="Home team name")
    away_team: str = Field(alias="strAwayTeam", description="Away team name")
    date: str = Field(alias="dateEvent", description="Match date")
    time: str = Field(alias="strTime", description="Match time")
    home_score: Optional[int] = Field(alias="intHomeScore", description="Home team score")
    away_score: Optional[int] = Field(alias="intAwayScore", description="Away team score")
    status: str = Field(alias="strStatus", description="Match status")
    team_stats: Dict[str, TeamStats] = Field(description="Team statistics")
    odds: MatchOdds = Field(description="Match odds")

    def is_live(self) -> bool:
        """Check if match is currently live."""
        return self.status.lower() in ["in play", "playing", "live"]

    def is_finished(self) -> bool:
        """Check if match is finished."""
        return self.status.lower() in ["finished", "ft", "completed"]

    def get_match_time(self) -> datetime:
        """Get match datetime."""
        return datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M:%S") 