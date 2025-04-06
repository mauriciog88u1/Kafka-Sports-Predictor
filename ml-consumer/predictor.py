def predict(match_data):
    home = match_data.get("home_team", "")
    away = match_data.get("away_team", "")
    home_score = int(match_data.get("home_score", 0))
    away_score = int(match_data.get("away_score", 0))

    if home_score > away_score:
        winner = home
    elif away_score > home_score:
        winner = away
    else:
        winner = "Draw"

    return {
        "match_id": match_data.get("match_id"),
        "prediction": winner
    }
