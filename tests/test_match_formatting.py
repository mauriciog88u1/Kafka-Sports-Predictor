"""Test match data formatting from UI to Kafka."""
import pytest
import httpx
import json
import logging
import ssl
import asyncio
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from src.utils.validation import SchemaValidator
from src.config import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test match IDs from recent matches
TEST_MATCH_IDS = [
    "2070169",  # Arsenal vs Crystal Palace (2025-04-23)
    "2070149",  # Arsenal vs Brentford (2025-04-12)
    "2235775",  # Arsenal vs Real Madrid (2025-04-08)
    "2070129",  # Arsenal vs Fulham (2025-04-01)
    "2070119"   # Arsenal vs Chelsea (2025-03-16)
]

@pytest.mark.asyncio
async def test_match_data_formatting():
    """Test that match data is properly formatted when sent from UI to backend."""
    validator = SchemaValidator()
    timeout = httpx.Timeout(30.0, connect=30.0)  # 30 seconds timeout
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Set up Kafka consumer
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP,
        group_id="test-consumer",
        auto_offset_reset="latest",
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
        sasl_plain_username=settings.KAFKA_USERNAME,
        sasl_plain_password=settings.KAFKA_PASSWORD,
        ssl_context=ssl_context,
        enable_auto_commit=True
    )
    await consumer.start()
    logger.debug("Kafka consumer started")
    
    try:
        # Send request to API
        async with httpx.AsyncClient(base_url="http://app:8000", timeout=timeout) as client:
            logger.debug("Sending request to API...")
            response = await client.post(
                "/api/v1/matches/batch",
                json={"match_ids": TEST_MATCH_IDS}
            )
            logger.debug(f"Received response with status code: {response.status_code}")
            
            # Log full response data
            data = response.json()
            logger.debug("API Response data:")
            logger.debug(json.dumps(data, indent=2))
            
            # Check response
            assert response.status_code == 200
            assert data["status"] == "success"
            assert data["processed"] == len(TEST_MATCH_IDS)
            
            # Wait for and validate Kafka messages
            logger.debug("Waiting for Kafka messages...")
            messages = []
            start_time = asyncio.get_event_loop().time()
            timeout_seconds = 30
            
            while len(messages) < len(TEST_MATCH_IDS):
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    logger.error(f"Timeout waiting for messages. Received {len(messages)} of {len(TEST_MATCH_IDS)}")
                    break
                    
                try:
                    msg = await asyncio.wait_for(consumer.getone(), timeout=5.0)
                    message_data = json.loads(msg.value.decode())
                    messages.append(message_data)
                    logger.debug("\nReceived Kafka message:")
                    logger.debug(json.dumps(message_data, indent=2))
                    
                    # Validate message format
                    validation_result = validator.validate_match_data(message_data)
                    if not validation_result.is_valid:
                        logger.error(f"Validation errors: {validation_result.errors}")
                        assert False, f"Invalid message format: {validation_result.errors}"
                    
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for message, continuing...")
                    continue
            
            # Validate each message
            for message_data in messages:
                try:
                    # Validate against our schema
                    validator.validate_match_update(message_data)
                    
                    # Check required fields
                    assert "match" in message_data
                    assert "home_team" in message_data
                    assert "away_team" in message_data
                    
                    match = message_data["match"]
                    home_team = message_data["home_team"]
                    away_team = message_data["away_team"]
                    
                    # Check match fields
                    assert "id" in match
                    assert "name" in match
                    assert "league" in match
                    assert "home_team" in match
                    assert "away_team" in match
                    assert "date" in match
                    assert "time" in match
                    assert "status" in match
                    
                    # Check status values
                    assert match["status"] in ["Not Started", "Live", "Finished", "Postponed", "Cancelled"]
                    
                    # Check score types and consistency with status
                    if match["status"] in ["Live", "Finished"]:
                        assert isinstance(match["home_score"], int)
                        assert isinstance(match["away_score"], int)
                    else:
                        assert match["home_score"] is None
                        assert match["away_score"] is None
                    
                    # Check team fields
                    for team in [home_team, away_team]:
                        assert "id" in team
                        assert "name" in team
                        assert "form" in team
                        
                        # Check form fields
                        form = team["form"]
                        assert "last_5" in form
                        assert "wins" in form
                        assert "draws" in form
                        assert "losses" in form
                        assert "goals_for" in form
                        assert "goals_against" in form
                        assert "form_rating" in form
                        
                        # Check form values
                        assert isinstance(form["last_5"], list)
                        assert len(form["last_5"]) <= 5
                        assert all(result in ["W", "D", "L"] for result in form["last_5"])
                        assert isinstance(form["wins"], int)
                        assert isinstance(form["draws"], int)
                        assert isinstance(form["losses"], int)
                        assert isinstance(form["goals_for"], int)
                        assert isinstance(form["goals_against"], int)
                        assert isinstance(form["form_rating"], float)
                        assert 0 <= form["form_rating"] <= 3
                    
                    logger.debug(f"\nValid match data for {match['name']}:")
                    logger.debug(json.dumps(message_data, indent=2))
                    
                except Exception as e:
                    logger.error(f"\nValidation failed for match {match.get('name', 'Unknown')}:")
                    logger.error(json.dumps(message_data, indent=2))
                    raise
                
            # Check that we received all expected messages
            assert len(messages) == len(TEST_MATCH_IDS), f"Expected {len(TEST_MATCH_IDS)} messages, got {len(messages)}"
            logger.info(f"Successfully processed {len(messages)} messages")
            
    finally:
        # Clean up
        await consumer.stop()
        logger.debug("Kafka consumer stopped")

if __name__ == "__main__":
    asyncio.run(test_match_data_formatting()) 