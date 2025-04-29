# Bet365 Sports Prediction API

A sports prediction API that calculates match odds and expected goals using data from TheSportsDB API.

## Architecture

### Data Flow
1. **Data Collection**
   - TheSportsDB API Integration
   - Endpoints Used:
     - `lookupevent`: Match details and basic statistics
     - `eventslast`: Historical match data (last 5 matches)
     - `lookupteam`: Team information and metadata

2. **Processing Pipeline**
   ```
   Client Request → FastAPI → SportsDB API → Kafka → Consumer
   ```

3. **Match Processing Flow**
   - Match Data Fetching
     - Basic match information
     - Team statistics
     - Historical performance
   
   - Data Validation
     - Schema validation
     - Data transformation
     - Error handling
   
   - Message Processing
     - Kafka message production
     - Consumer message handling
     - Logging and monitoring

### Technology Stack

- **Backend**: FastAPI
- **Message Queue**: Kafka
- **Containerization**: Docker
- **Infrastructure**: Local Development

## Current Implementation

1. **API Endpoints**
   - `POST /api/v1/matches/batch`: Process multiple matches
   - Response includes processed count and errors

2. **Data Processing**
   - Match data fetching from TheSportsDB
   - Data validation using JSON schemas
   - Kafka message production/consumption

3. **Kafka Integration**
   - Topic: `match_predictions`
   - Producer: Sends validated match data
   - Consumer: Processes incoming messages

## Development Status

1. **Completed**
   - Basic project structure
   - TheSportsDB API integration
   - Data models and schemas
   - Kafka setup and integration
   - Batch processing endpoint
   - Message consumer implementation

2. **In Progress**
   - Message processing logic
   - Error recovery mechanisms
   - Monitoring and metrics
   - Testing improvements

3. **Next Steps**
   - Implement prediction calculations
   - Add persistence layer
   - Enhance error handling
   - Add comprehensive monitoring

## Setup and Installation

1. **Environment Setup**
   ```bash
   # Clone repository
   git clone [repository-url]
   cd bet365

   # Start services
   docker compose up -d
   ```

2. **Configuration**
   - Copy `.env.example` to `.env`
   - Add your TheSportsDB API key
   - Configure Kafka settings

3. **Running Tests**
   ```bash
   # Run test script
   docker compose exec app python scripts/test_match_formatting.py
   ```

## API Documentation

### Endpoints

1. **Match Processing**
   ```
   POST /api/v1/matches/batch
   Request Body:
   {
     "match_ids": ["2070169", "2070149"]
   }
   
   Response:
   {
     "processed": 2,
     "errors": []
   }
   ```

### Data Models

1. **Match Data**
   - Match ID
   - Teams
   - Date and time
   - Scores
   - Status
   - Statistics

2. **Team Statistics**
   - Form metrics
   - Performance data
   - Historical results

## Testing

1. **Test Flow**
   ```
   Test Script → API → Kafka → Logs
   ```
   - Test script sends match IDs
   - API processes and sends to Kafka
   - Consumer logs messages
   - Logs can be checked for verification

2. **Current Test Cases**
   - Batch processing
   - Data validation
   - Kafka integration
   - Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

TBD 