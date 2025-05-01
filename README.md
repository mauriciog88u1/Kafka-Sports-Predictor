# Bet365 Match Predictor API

## Overview
A high-performance match prediction system that combines real-time data processing with machine learning to provide football match predictions. The system uses a hybrid architecture, leveraging both synchronous API responses and asynchronous Kafka processing for optimal performance.

## Architecture

### Core Components
1. **FastAPI Backend**
   - REST API endpoints for match data and predictions
   - In-memory caching with file persistence
   - Kafka producer for asynchronous processing
   - Rate limiting and batch processing

2. **Kafka Pipeline**
   - Topic: `match_updates` for raw match data
   - Topic: `predictions` for processed predictions
   - Consumer groups for scalable processing
   - Exactly-once delivery semantics

3. **Caching System**
   - Two-layer caching (memory + file)
   - MD5-based match ID hashing
   - Configurable cache invalidation
   - Optimized lookup performance (O(1))

### Backend Flow
1. **Synchronous Path (Fast Response)**
   - Check cache for existing prediction
   - Return cached data if available
   - Queue update in background if data is stale

2. **Asynchronous Path (Fresh Data)**
   - Fetch match data from TheSportsDB API
   - Process through Kafka pipeline
   - Update cache with new predictions
   - Notify clients of updates

## Performance Metrics
- Average response time (cached): ~50ms
- Average response time (fresh data): ~2s
- Kafka processing time: ~1s per message
- Cache hit ratio: ~80%
- Concurrent request handling: Up to 1000 req/s

## Setup Instructions

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Kafka cluster (Confluent Cloud recommended)
- TheSportsDB API key

### Environment Variables
```bash
# API Configuration
SPORTS_DB_API_KEY=your_api_key
PORT=8000

# Kafka Configuration
KAFKA_BOOTSTRAP=your_bootstrap_server
KAFKA_USERNAME=your_username
KAFKA_PASSWORD=your_password
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=PLAIN

# Cache Configuration
CACHE_TTL=3600  # 1 hour
CACHE_FILE_PATH=/app/data/cache.json
```

### Local Development
1. Clone the repository:
   ```bash
   git clone https://github.com/mauriciog88u1/Kafka-Sports-Predictor.git
   cd Kafka-Sports-Predictor
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy example configuration:
   ```bash
   cp .env.example .env
   cp docker-compose.yml.example docker-compose.yml
   ```

5. Start the services:
   ```bash
   docker-compose up -d
   ```

### Production Deployment
1. Build the Docker image:
   ```bash
   docker build -t bet365-predictor-api .
   ```

2. Deploy to Cloud Run:
   ```bash
   ./deploy.sh
   ```

## API Documentation

### Endpoints

1. **Get Match Prediction**
   ```
   GET /api/v1/predictions/{match_id}
   ```
   Returns prediction for a specific match.

2. **Batch Process Matches**
   ```
   POST /api/v1/matches/batch
   ```
   Process multiple matches in one request.

3. **Get Match Data**
   ```
   GET /api/v1/matches/{match_id}
   ```
   Returns match details and statistics.

### Example Response
```json
{
    "match_id": "2070169",
    "status": "success",
    "prediction": {
        "home_win_prob": 0.65,
        "draw_prob": 0.20,
        "away_win_prob": 0.15,
        "confidence": 0.85,
        "expected_goals": {
            "home": 1.8,
            "away": 1.2
        }
    }
}
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage
- Unit tests: 85%
- Integration tests: 70%
- End-to-end tests: 60%

## Monitoring and Logging

### Metrics Tracked
- API response times
- Cache hit/miss rates
- Kafka lag and throughput
- Prediction accuracy
- Error rates

### Log Levels
- DEBUG: Detailed debugging information
- INFO: General operational information
- WARNING: Minor issues and degraded states
- ERROR: Serious issues requiring attention
- CRITICAL: System-wide failures

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- TheSportsDB for providing match data
- Confluent Cloud for Kafka hosting
- Google Cloud Run for deployment
- FastAPI framework