# Bet365 Predictor API Schema

## Base URL
```
https://bet365-predictor-api-806378004153.us-central1.run.app
```

## Endpoints

### 1. Get Match Prediction
Get prediction for a specific match.

**Endpoint:** `GET /api/v1/predictions/{match_id}`

**Path Parameters:**
- `match_id` (string, required): The ID of the match to get prediction for

**Response Format:**
```json
{
    "match_id": "2070169",
    "status": "success",
    "prediction": {
        "home_win_probability": 0.77,  // Probability of home team winning (0-1)
        "draw_probability": 0.12,      // Probability of a draw (0-1)
        "away_win_probability": 0.12,  // Probability of away team winning (0-1)
        "expected_goals": {
            "home": 1.9,               // Expected goals for home team
            "away": 1.41               // Expected goals for away team
        },
        "btts_probability": 0.67,      // Probability of Both Teams To Score (0-1)
        "predicted_score": "2-1",      // Predicted final score
        "confidence": "medium"         // Confidence level: "high", "medium", or "low"
    }
}
```

### 2. Get Batch Match Data
Get data for multiple matches in a single request.

**Endpoint:** `POST /api/v1/matches/batch`

**Request Body:**
```json
{
    "match_ids": ["2070169", "2070149", "2235775"]
}
```

**Response Format:**
```json
{
    "status": "success",
    "processed": 3,
    "errors": [],
    "results": [
        {
            "idEvent": "2070169",
            "strEvent": "Arsenal vs Crystal Palace",
            "strLeague": "English Premier League",
            "idLeague": "4328",
            "strSeason": "2024-2025",
            "idHomeTeam": "133604",
            "strHomeTeam": "Arsenal",
            "idAwayTeam": "133632",
            "strAwayTeam": "Crystal Palace",
            "dateEvent": "2025-04-23",
            "strTime": "19:00:00",
            "strTimestamp": "2025-04-23T19:00:00",
            "intHomeScore": 2,
            "intAwayScore": 2,
            "strStatus": "Finished",
            "team_stats": {
                "home": {
                    "form": {
                        "last_5": ["W", "D", "W", "W", "D"],
                        "wins": 3,
                        "draws": 2,
                        "losses": 0,
                        "goals_scored": 10,
                        "goals_conceded": 4,
                        "clean_sheets": 2,
                        "failed_to_score": 0,
                        "form_score": 67.7
                    },
                    "xg_for": 1.8,
                    "xg_against": 1.2,
                    "avg_goals_scored": 1.6,
                    "avg_goals_conceded": 0.8,
                    "win_probability": 0.6
                },
                "away": {
                    "form": {
                        "last_5": ["L", "D", "D", "L", "L"],
                        "wins": 0,
                        "draws": 2,
                        "losses": 3,
                        "goals_scored": 4,
                        "goals_conceded": 15,
                        "clean_sheets": 1,
                        "failed_to_score": 3,
                        "form_score": 0
                    },
                    "xg_for": 1.5,
                    "xg_against": 1.4,
                    "avg_goals_scored": 1.4,
                    "avg_goals_conceded": 1.0,
                    "win_probability": 0.4
                }
            },
            "odds": {
                "home_win": 2.0,
                "draw": 3.5,
                "away_win": 4.0,
                "over_2_5": 1.8,
                "under_2_5": 2.0,
                "btts_yes": 1.9,
                "btts_no": 1.9
            }
        }
    ]
}
```

## Frontend Display Guidelines

### 1. Match Prediction Display
- Display probabilities as percentages (e.g., 77% instead of 0.77)
- Use color coding for probabilities:
  - High probability (>70%): Green
  - Medium probability (40-70%): Yellow
  - Low probability (<40%): Red
- Show confidence level with an icon:
  - High: 🔵
  - Medium: 🟡
  - Low: 🔴

### 2. Expected Goals Display
- Show as a bar chart comparing home vs away
- Include the predicted score prominently
- Use color gradients to show probability distribution

### 3. BTTS Probability Display
- Show as a percentage
- Use a progress bar or gauge visualization
- Color code based on probability:
  - >70%: Green
  - 40-70%: Yellow
  - <40%: Red

### 4. Team Stats Display
- Show form as a sequence of icons (W/D/L)
- Display goals scored/conceded as bar charts
- Show clean sheets and failed to score as badges
- Use team badges/logos where available

### 5. Error Handling
- Display user-friendly error messages
- Show loading states during API calls
- Handle network errors gracefully
- Provide retry options for failed requests

## Example Frontend Layout

```
+------------------------------------------+
|  Match: Arsenal vs Crystal Palace        |
|  League: English Premier League          |
|  Date: 2025-04-23 19:00                 |
+------------------------------------------+
|                                          |
|  Win Probability:                        |
|  [77% 🔵] Arsenal                        |
|  [12% 🔴] Draw                           |
|  [12% 🔴] Crystal Palace                 |
|                                          |
|  Expected Goals:                         |
|  Arsenal: [=====] 1.9                   |
|  Crystal Palace: [===] 1.41             |
|                                          |
|  Predicted Score: 2-1                    |
|                                          |
|  BTTS Probability: [=======] 67%         |
|                                          |
|  Team Form:                              |
|  Arsenal: W D W W D                      |
|  Crystal Palace: L D D L L               |
+------------------------------------------+
```

## Notes
- All probabilities are between 0 and 1
- Times are in UTC
- Team names and league names are standardized
- Form is shown as last 5 matches (W=Win, D=Draw, L=Loss)
- Confidence levels are based on data quality and uncertainty 