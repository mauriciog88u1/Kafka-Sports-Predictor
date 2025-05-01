# Bet365 Match Predictor Demo

This is version 2 of a football match prediction demo. The main changes are in the backend architecture and UI design, while keeping the core prediction model and Kafka integration.

## Original Version (v1)
- Basic React frontend at mauric10.com/bet365
- Kafka-based async processing
- Basic prediction model
- Google Cloud Run deployment

## Current Version (v2) Changes
- Redesigned UI to match Bet365's style
- Improved backend architecture:
  - Added caching layer for faster responses
  - Enhanced Kafka message processing
  - Better error handling
  - Optimized API performance
- Same core prediction model using:
  - Team form
  - Recent results
  - Goals scored/conceded
  - Home/away performance

## Backend Flow
1. UI sends match IDs to API
2. API layer:
   - Checks cache for existing predictions
   - If not cached:
     - Fetches match data from TheSportsDB
     - Calculates initial form scores
     - Produces message to Kafka topic
   - Returns immediate response with available data
3. Kafka Consumer:
   - Processes match data asynchronously
   - Runs full prediction calculations
   - Updates cache with final predictions
4. UI can fetch updated predictions

## Technical Details

### Base URL
```
https://bet365-predictor-api-806378004153.us-central1.run.app
```

### API Endpoints
```
POST /api/v1/matches/batch
- Process multiple matches in one request
- Body: { "match_ids": ["2070186", "2070178"] }
- Returns predictions with form analysis
- Produces messages to Kafka for async processing

GET /api/v1/leagues/{league_id}/matches
- Get all matches for a league
- Includes cached predictions if available

GET /api/v1/teams/{team_id}/form
- Get team form and recent performance
- Used by UI for quick form display
```

### Kafka Integration
- Topic: match_predictions
- Producer: FastAPI service
- Consumer: Separate service on Cloud Run
- Message format: JSON with match data and predictions
- Async processing for heavy calculations

### Performance
- Average response times:
  - Cached requests: ~100ms
  - New requests with cache miss: ~1-2s
  - Async updates via Kafka: ~2-3s
- Cache hit rate: ~80%
- Supports batches of up to 20 matches

## Learnings & Trade-offs

### What Worked Well
1. Hybrid Caching + Kafka approach:
   - Fast initial responses from cache
   - Async processing for heavy calculations
   - Reliable message processing

2. Cloud Run deployment:
   - Easy scaling
   - Cost-effective
   - Simple maintenance

3. Batch processing:
   - Reduced API calls
   - Better user experience
   - Efficient Kafka message batching

### What I'd Do Differently
1. Data Storage:
   - Use Redis instead of file cache
   - Add proper database for match history
   - Implement cache invalidation strategy

2. Architecture:
   - Add WebSocket for real-time updates
   - Implement better error recovery
   - Add monitoring and alerting

3. Prediction Model:
   - Add machine learning components
   - Include more historical data
   - Consider weather and player stats

### Known Limitations
- File cache doesn't work well with multiple instances
- No rate limiting on TheSportsDB API calls
- Basic prediction model
- Limited historical data usage

## Demo Features
- Live match predictions
- Real-time data from TheSportsDB
- Hybrid caching + Kafka processing
- Scalable Cloud Run deployment

## Setup
Check `deploy.sh.example` and `docker-compose.yml.example` for deployment configuration. You'll need:
- A TheSportsDB API key
- Kafka credentials (required)
- Google Cloud project

## Note
This is a demonstration project and should not be used in production without proper modifications and security considerations. 