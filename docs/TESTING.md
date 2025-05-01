# Testing Documentation

## Overview
This document details the testing approach, structure, and examples for the Bet365 Match Predictor API.

## Test Structure
```
tests/
├── unit/                     # Unit tests for individual components
│   ├── test_api.py          # API endpoint tests
│   ├── test_ml.py           # Machine learning model tests
│   └── test_cache.py        # Caching logic tests
├── integration/             # Integration tests
│   ├── test_kafka.py        # Kafka pipeline tests
│   └── test_sports_db.py    # External API integration tests
├── fixtures/               # Test fixtures and mock data
│   └── responses/          # Mock API responses
└── conftest.py            # Test configuration and fixtures
```

## Testing Approach

### 1. Unit Tests
Individual component testing with mocked dependencies and focus on business logic.

Example unit test:
```python
@pytest.mark.asyncio
async def test_prediction_calculation():
    mock_data = load_fixture("match_data.json")
    prediction = await calculate_prediction(mock_data)
    assert "home_win_prob" in prediction
    assert 0 <= prediction["home_win_prob"] <= 1
```

Key areas covered:
- Prediction calculation logic
- Cache operations
- Data validation
- Schema validation

### 2. Integration Tests
Testing component interactions and end-to-end flows.

Example integration test:
```python
@pytest.mark.asyncio
async def test_batch_processing():
    match_ids = ["12345", "67890"]
    response = await client.post(
        "/api/v1/matches/batch",
        json={"match_ids": match_ids}
    )
    assert response.status_code == 200
    assert len(response.json()["predictions"]) == 2
```

Key areas covered:
- API endpoints
- Kafka producer/consumer flow
- External API integration
- Cache integration

### 3. Mock Responses
Example mock response structure:
```json
{
  "match_id": "12345",
  "api_response": {
    "success": true,
    "data": { ... }
  },
  "rate_limit_remaining": 10
}
```

Areas covered:
- API responses
- Rate limit scenarios
- Error cases
- Cache hits/misses

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

### Current Coverage
- Unit tests: 85%
- Integration tests: 70%

### CI/CD Integration
Tests are automatically run on:
- Pull requests
- Merges to main branch
- Release tags

## Test Configuration

### Environment Setup
```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install test dependencies
pip install -r requirements/test.txt
```

### Mock Configuration
```python
# Example mock configuration in conftest.py
@pytest.fixture
def mock_sports_db():
    with patch("src.api.services.sports_db.get_match_data") as mock:
        mock.return_value = load_fixture("match_data.json")
        yield mock
```

## Best Practices

1. **Async Testing**
   - Use `pytest.mark.asyncio` for async tests
   - Properly mock async dependencies
   - Handle event loop cleanup

2. **Mocking**
   - Mock external services
   - Use appropriate fixtures
   - Maintain realistic test data

3. **Test Data**
   - Keep fixtures up to date
   - Use realistic data samples
   - Cover edge cases

4. **Performance**
   - Use test parallelization
   - Optimize slow tests
   - Cache test dependencies 