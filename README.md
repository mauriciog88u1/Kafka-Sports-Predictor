# Bet365 Match Predictor API

## Overview
A high-performance match prediction system that combines real-time data processing with machine learning to provide football match predictions. The system uses a hybrid architecture, leveraging both synchronous API responses and asynchronous Kafka processing for optimal performance.

## Project Structure
```
bet365-predictor/
├── src/                              # Application source code
│   ├── api/                          # API implementation
│   │   ├── consumers/                # Kafka consumers
│   │   │   ├── __init__.py
│   │   │   └── match_consumer.py     # Match data consumer
│   │   ├── routes/                   # API routes
│   │   │   ├── __init__.py
│   │   │   ├── matches.py           # Match endpoints
│   │   │   └── predictions.py        # Prediction endpoints
│   │   └── services/                 # Business logic
│   │       ├── sports_db.py         # Sports data service
│   │       └── cache.py             # Caching service
│   ├── models/                       # Data models
│   │   ├── __init__.py
│   │   ├── match.py                 # Match model
│   │   └── prediction.py            # Prediction model
│   ├── ml/                          # Machine learning components
│   │   ├── __init__.py
│   │   ├── expected_goals.py        # xG calculator
│   │   └── odds_calculator.py       # Odds calculator
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       └── validation.py            # Data validation
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   │   ├── test_api.py
│   │   └── test_ml.py
│   ├── integration/                 # Integration tests
│   │   └── test_kafka.py
│   ├── fixtures/                    # Test fixtures
│   │   └── match_data.json
│   └── conftest.py                  # Test configuration
├── scripts/                         # Utility scripts
│   ├── setup_env.sh                # Environment setup
│   └── run_tests.sh                # Test runner
├── migrations/                      # Database migrations
│   ├── versions/
│   └── env.py
├── docs/                           # Documentation
│   ├── API_SCHEMA.md              # API documentation
│   └── DEPLOYMENT.md              # Deployment guide
├── .github/                        # GitHub configurations
│   └── workflows/                  # CI/CD workflows
├── docker/                         # Docker configurations
│   ├── Dockerfile                 # API service Dockerfile
│   └── docker-compose.yml         # Local development setup
├── config/                         # Configuration files
│   ├── .env.example              # Environment variables template
│   └── alembic.ini               # Migration configuration
├── requirements/                   # Dependencies
│   ├── base.txt                  # Common dependencies
│   ├── dev.txt                   # Development dependencies
│   └── prod.txt                  # Production dependencies
├── .gitignore                     # Git ignore rules
├── README.md                      # Project documentation
└── setup.py                       # Package setup
```

### Directory Structure Explanation

#### Core Application (`src/`)
- `api/`: FastAPI application implementation
  - `consumers/`: Kafka consumers for async processing
  - `routes/`: API endpoint definitions
  - `services/`: Business logic and external services
- `models/`: Pydantic models and database schemas
- `ml/`: Machine learning components and algorithms
- `utils/`: Shared utility functions

#### Testing (`tests/`)
- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for system flows
- `fixtures/`: Test data and fixtures
- All test files follow `test_*.py` naming convention

#### Configuration (`config/`)
- Environment variable templates
- Database migration settings
- Separate configs for development and production

#### Documentation (`docs/`)
- API documentation and schemas
- Deployment and setup guides
- Architecture documentation

#### Infrastructure
- `docker/`: All Docker-related configurations
- `migrations/`: Database migration scripts
- `scripts/`: Utility and automation scripts
- `requirements/`: Separated dependency files

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

1. **Match Data Processing**
   ```python
   # src/api/services/sports_db.py
   async def get_match_data(match_id: str, cache: Dict[str, Any]):
       # 1. Check cache for existing data
       # 2. If cache miss, fetch from TheSportsDB API:
       #    - Match details
       #    - Team information
       #    - Historical matches
       # 3. Calculate form and statistics
       # 4. Transform and cache data
   ```

2. **Team Statistics Calculation**
   ```python
   # src/ml/expected_goals.py
   class ExpectedGoalsCalculator:
       def calculate(self, data: Dict[str, Any]):
           # 1. Calculate base xG from team stats
           # 2. Apply league-specific factors
           # 3. Adjust using historical data
           # 4. Normalize within reasonable bounds
   ```

3. **Prediction Generation**
   ```python
   # src/api/consumers/match_consumer.py
   async def calculate_prediction(match_data: Dict[str, Any]):
       # 1. Extract team statistics
       # 2. Calculate team strengths:
       #    - Form score (40% weight)
       #    - Goals ratio (30% weight)
       #    - xG ratio (30% weight)
       # 3. Apply home advantage (10% boost)
       # 4. Calculate probabilities and confidence
   ```

4. **Odds Calculation**
   ```python
   # src/ml/odds_calculator.py
   class OddsCalculator:
       def calculate_match_odds(self, match: Match):
           # 1. Calculate win probabilities
           # 2. Calculate goals probabilities
           # 3. Calculate BTTS probabilities
           # 4. Convert to odds with margin
   ```

5. **Kafka Integration**
   - **Producer** (API Service):
     ```python
     # When new match data arrives:
     await producer.send(
         topic="match_updates",
         value=match_data
     )
     ```
   - **Consumer** (Prediction Service):
     ```python
     async for msg in consumer:
         # 1. Validate message format
         # 2. Calculate prediction
         # 3. Update cache
         # 4. Send to output topic
     ```

6. **Caching System**
   - Two-layer approach:
     1. In-memory cache for fast access
     2. File-based persistence for durability
   - Cache structure:
     ```python
     cache = {
         "matches": {
             "match_id": {
                 "data": match_data,
                 "timestamp": cache_time,
                 "prediction": prediction_result
             }
         },
         "leagues": {
             "league_id": [match_data_list]
         }
     }
     ```

7. **Response Flow**
   ```python
   @app.get("/api/v1/predictions/{match_id}")
   async def get_prediction(match_id: str):
       # 1. Check cache for prediction
       # 2. If not found or stale:
       #    - Fetch fresh match data
       #    - Calculate quick prediction
       #    - Queue for detailed analysis
       # 3. Return prediction with confidence
   ```

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