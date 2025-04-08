def predict(match_data):
    # This function predicts the outcome of a match based on the provided data.
    # It uses a simple heuristic based on the team names and round number.
    #in the future the match_data will include previous team matchup data and player starts then use a random forest
    home_team = match_data.get("strHomeTeam", "")
    away_team = match_data.get("strAwayTeam", "")

    if not home_team or not away_team:
        return {"match_id": match_data.get("match_id"), "prediction": "N/A"}

    try:
        round_num = int(match_data.get("intRound", "1"))
    except ValueError:
        round_num = 1

    home_score = 10  # home team gets a baseline advantage
    away_score = 0  # away team has no baseline advantage

    # Add the sum of ASCII values for the team names.
    home_score += sum(ord(c) for c in home_team)
    away_score += sum(ord(c) for c in away_team)


    adjustment = (round_num - 1) * 0.5
    home_score -= adjustment
    away_score -= adjustment

    # Determine the outcome.
    if home_score > away_score:
        winner = home_team
    elif away_score > home_score:
        winner = away_team
    else:
        winner = "Draw"

    return {"match_id": match_data.get("match_id"), "prediction": winner}
