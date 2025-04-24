from ml_model import MatchPredictor

# Create a singleton instance of the predictor
predictor = MatchPredictor()

def predict(match_data):
    """
    Predict match outcome using statistical analysis of historical patterns.
    Uses:
    - Home/Away win rates
    - Team form (last 5 matches)
    - League position impact
    - Goals scored/conceded patterns
    """
    home_team = match_data.get("strHomeTeam", "")
    away_team = match_data.get("strAwayTeam", "")
    
    if not home_team or not away_team:
        return "N/A"
    
    # Get match history
    match_history = match_data.get("matchHistory", [])
    league_table = match_data.get("leagueTable", [])
    
    # Initialize scores
    home_score = 0
    away_score = 0
    
    # 1. Home/Away Advantage Analysis
    home_games = 0
    home_wins = 0
    away_games = 0
    away_wins = 0
    
    for match in match_history:
        # Home team analysis
        if match.get("strHomeTeam") == home_team:
            home_games += 1
            if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                home_wins += 1
        elif match.get("strAwayTeam") == home_team:
            if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                home_wins += 1
                
        # Away team analysis
        if match.get("strHomeTeam") == away_team:
            away_games += 1
            if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                away_wins += 1
        elif match.get("strAwayTeam") == away_team:
            if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                away_wins += 1
    
    # Calculate win rates
    home_win_rate = (home_wins / max(home_games, 1)) * 100
    away_win_rate = (away_wins / max(away_games, 1)) * 100
    
    # Add win rate points (weighted more heavily for home team)
    home_score += home_win_rate * 1.5  # Home advantage multiplier
    away_score += away_win_rate
    
    # 2. Recent Form Analysis (last 5 matches)
    recent_matches = match_history[:5]  # Get last 5 matches
    home_recent_wins = 0
    away_recent_wins = 0
    
    for match in recent_matches:
        if match.get("strHomeTeam") == home_team:
            if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                home_recent_wins += 1
        elif match.get("strAwayTeam") == home_team:
            if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                home_recent_wins += 1
                
        if match.get("strHomeTeam") == away_team:
            if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                away_recent_wins += 1
        elif match.get("strAwayTeam") == away_team:
            if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                away_recent_wins += 1
    
    # Add recent form points (weighted more heavily)
    home_score += home_recent_wins * 20
    away_score += away_recent_wins * 20
    
    # 3. League Position Analysis
    home_position = 20
    away_position = 20
    home_points = 0
    away_points = 0
    
    for team in league_table:
        if team.get("strTeam") == home_team:
            home_position = int(team.get("intRank", 20))
            home_points = int(team.get("intPoints", 0))
        elif team.get("strTeam") == away_team:
            away_position = int(team.get("intRank", 20))
            away_points = int(team.get("intPoints", 0))
    
    # Add league position points (higher position = more points)
    home_score += (21 - home_position) * 5
    away_score += (21 - away_position) * 5
    
    # Add points difference
    points_diff = home_points - away_points
    home_score += points_diff * 0.5
    away_score -= points_diff * 0.5
    
    # 4. Goals Analysis
    home_goals_scored = 0
    home_goals_conceded = 0
    away_goals_scored = 0
    away_goals_conceded = 0
    
    for team in league_table:
        if team.get("strTeam") == home_team:
            home_goals_scored = int(team.get("intGoalsFor", 0))
            home_goals_conceded = int(team.get("intGoalsAgainst", 0))
        elif team.get("strTeam") == away_team:
            away_goals_scored = int(team.get("intGoalsFor", 0))
            away_goals_conceded = int(team.get("intGoalsAgainst", 0))
    
    # Add goals difference points
    home_score += (home_goals_scored - home_goals_conceded) * 0.5
    away_score += (away_goals_scored - away_goals_conceded) * 0.5
    
    # Determine the outcome
    if home_score > away_score:
        return home_team
    elif away_score > home_score:
        return away_team
    else:
        return "Draw"
