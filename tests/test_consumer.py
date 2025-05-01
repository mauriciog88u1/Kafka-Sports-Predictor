"""Test Kafka consumer functionality."""
import asyncio
import json
import os
import pytest
import ssl
from unittest.mock import AsyncMock, patch
from aiokafka import AIOKafkaProducer
from src.api.consumers.match_consumer import consume_matches, calculate_odds
from src.config import settings

@pytest.fixture
def mock_match_data():
    """Sample match data for testing."""
    return {
        "idEvent": "12345",
        "strEvent": "Test Match",
        "idHomeTeam": "133602",
        "idAwayTeam": "133601",
        "strHomeTeam": "Test Home Team",
        "strAwayTeam": "Test Away Team",
        "strLeague": "Premier League",
        "dateEvent": "2024-04-30",
        "strTime": "20:00:00",
        "team_stats": {
            "home": {
                "form": {"form_score": 75},
                "avg_goals_scored": 2.1,
                "avg_goals_conceded": 1.2,
                "xg_for": 2.0,
                "xg_against": 1.1
            },
            "away": {
                "form": {"form_score": 65},
                "avg_goals_scored": 1.8,
                "avg_goals_conceded": 1.5,
                "xg_for": 1.7,
                "xg_against": 1.3
            }
        }
    }

@pytest.fixture
async def kafka_producer():
    """Create a Kafka producer with the correct configuration."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP,
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
        sasl_plain_username=settings.KAFKA_USERNAME,
        sasl_plain_password=settings.KAFKA_PASSWORD,
        ssl_context=context,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    await producer.start()
    yield producer
    await producer.stop()

@pytest.mark.asyncio
async def test_calculate_odds(mock_match_data):
    """Test odds calculation functionality."""
    # Calculate odds
    odds = await calculate_odds(mock_match_data)
    
    # Verify odds are calculated correctly
    assert isinstance(odds, dict)
    assert "home" in odds
    assert "draw" in odds
    assert "away" in odds
    assert all(isinstance(v, float) for v in odds.values())
    assert all(v > 1.0 for v in odds.values())  # Odds should be greater than 1.0
    
    # Verify odds are reasonable
    assert 1.0 < odds["home"] < 10.0
    assert 1.0 < odds["draw"] < 10.0
    assert 1.0 < odds["away"] < 10.0

@pytest.mark.asyncio
async def test_consumer_process_message(mock_match_data, kafka_producer):
    """Test consumer message processing."""
    # Send test message
    await kafka_producer.send(settings.KAFKA_TOPIC, mock_match_data)
    await kafka_producer.flush()
    
    # Mock the consumer to process one message
    with patch('src.api.consumers.match_consumer.AIOKafkaConsumer') as mock_consumer:
        # Create a mock message
        mock_msg = AsyncMock()
        mock_msg.value = mock_match_data
        
        # Configure the mock consumer
        mock_consumer_instance = AsyncMock()
        mock_consumer_instance.__aiter__.return_value = [mock_msg]
        mock_consumer.return_value = mock_consumer_instance
        
        # Run the consumer
        consumer_task = asyncio.create_task(consume_matches())
        
        # Wait for the consumer to process the message
        await asyncio.sleep(1)
        
        # Cancel the consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify the consumer processed the message
        mock_consumer_instance.start.assert_called_once()
        mock_consumer_instance.stop.assert_called_once()

@pytest.mark.asyncio
async def test_consumer_error_handling():
    """Test consumer error handling."""
    with patch('src.api.consumers.match_consumer.AIOKafkaConsumer') as mock_consumer:
        # Configure the mock consumer to raise an exception
        mock_consumer_instance = AsyncMock()
        mock_consumer_instance.__aiter__.side_effect = Exception("Test error")
        mock_consumer.return_value = mock_consumer_instance
        
        # Run the consumer
        consumer_task = asyncio.create_task(consume_matches())
        
        # Wait for the consumer to process the message
        await asyncio.sleep(1)
        
        # Cancel the consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify the consumer handled the error
        mock_consumer_instance.start.assert_called_once()
        mock_consumer_instance.stop.assert_called_once()

@pytest.mark.asyncio
async def test_consumer_invalid_message():
    """Test consumer handling of invalid messages."""
    with patch('src.api.consumers.match_consumer.AIOKafkaConsumer') as mock_consumer:
        # Create an invalid message
        invalid_msg = AsyncMock()
        invalid_msg.value = {"invalid": "data"}  # Missing required fields
        
        # Configure the mock consumer
        mock_consumer_instance = AsyncMock()
        mock_consumer_instance.__aiter__.return_value = [invalid_msg]
        mock_consumer.return_value = mock_consumer_instance
        
        # Run the consumer
        consumer_task = asyncio.create_task(consume_matches())
        
        # Wait for the consumer to process the message
        await asyncio.sleep(1)
        
        # Cancel the consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        # Verify the consumer handled the invalid message
        mock_consumer_instance.start.assert_called_once()
        mock_consumer_instance.stop.assert_called_once() 