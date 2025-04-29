# Match Prediction API Documentation

## Overview
This API provides endpoints for match predictions and updates. The system processes match data through Kafka and returns predictions via REST endpoints.

## Endpoints

### 1. Get Prediction
```
GET /api/v1/predictions/{match_id}
```

Retrieves the latest prediction for a specific match.

#### Response
```json
{
  "match_id": "12345",
  "home_win_prob": 0.45,
  "draw_prob": 0.25,
  "away_win_prob": 0.30,
  "confidence": 0.85,
  "timestamp": "2024-03-20T15:30:00Z",
  "model_version": "1.0.0",
  "additional_info": {
    "expected_goals_home": 1.8,
    "expected_goals_away": 1.2,
    "key_factors": [
      "Home team recent form",
      "Head to head record",
      "Injuries"
    ]
  }
}
```

### 2. Get Match Updates
```
GET /api/v1/matches/{match_id}/updates
```

Retrieves the latest updates for a specific match.

#### Response
```json
{
  "idEvent": "12345",
  "strEvent": "Team A vs Team B",
  "strLeague": "Premier League",
  "strHomeTeam": "Team A",
  "strAwayTeam": "Team B",
  "dateEvent": "2024-03-20",
  "strTime": "20:00:00",
  "intHomeScore": 1,
  "intAwayScore": 0,
  "strStatus": "Live",
  "odds": {
    "home": 2.5,
    "draw": 3.2,
    "away": 2.8
  }
}
```

## Kafka Integration

### Topic: match_updates
The frontend should send match updates to this Kafka topic. The message format should follow the [Match Update Schema](schemas/match_update.json).

### Example Producer Code
```javascript
const producer = new KafkaProducer({
  brokers: ['kafka:9092']
});

await producer.send({
  topic: 'match_updates',
  messages: [{
    value: JSON.stringify({
      idEvent: '12345',
      strEvent: 'Team A vs Team B',
      // ... other fields as per schema
    })
  }]
});
```

## Error Handling

### HTTP Status Codes
- 200: Success
- 400: Bad Request (invalid input)
- 404: Not Found (match not found)
- 500: Internal Server Error

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details if available
    }
  }
}
```

## Rate Limiting
- 100 requests per minute per IP address
- 1000 requests per hour per API key

## Authentication
All API requests require an API key in the header:
```
Authorization: Bearer your-api-key
```

## Versioning
API version is included in the URL path (e.g., `/api/v1/`). Breaking changes will result in a new version number. 