"""Test match data formatting directly."""
import asyncio
import httpx
import json
import logging
from src.utils.validation import SchemaValidator
from src.utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Test match IDs from recent matches
TEST_MATCH_IDS = [
    "2070169",  # Arsenal vs Crystal Palace (2025-04-23)
    "2070149",  # Arsenal vs Brentford (2025-04-12)
    "2235775",  # Arsenal vs Real Madrid (2025-04-08)
    "2070129",  # Arsenal vs Fulham (2025-04-01)
    "2070119"   # Arsenal vs Chelsea (2025-03-16)
]

async def test_match_formatting():
    """Test match data formatting."""
    validator = SchemaValidator()
    async with httpx.AsyncClient(base_url="http://app:8000", timeout=30.0) as client:
        logger.info("\nSending match IDs to backend...")
        logger.info(f"Match IDs: {TEST_MATCH_IDS}")
        
        try:
            # Send batch request
            response = await client.post(
                "/api/v1/matches/batch",
                json={"match_ids": TEST_MATCH_IDS}
            )
            
            # Check response
            if response.status_code != 200:
                logger.error(f"HTTP Error {response.status_code}")
                logger.error(f"Response: {response.text}")
                return
                
            data = response.json()
            logger.info(f"\nResponse status: {data['status']}")
            logger.info(f"Processed matches: {data['processed']}")
            
            if "errors" in data and data["errors"]:
                logger.error("\nErrors encountered:")
                for error in data["errors"]:
                    logger.error(f"- Match {error['match_id']}: {error['error']}")
            
            # Get the transformed data
            transformed_data = data.get("results", [])
            
            if not transformed_data:
                logger.error("No match data returned")
                return
            
            # Validate each match
            for match_data in transformed_data:
                logger.info("\n" + "="*50)
                logger.info(f"Validating match: {match_data['strEvent']}")
                
                try:
                    # Validate against schema
                    validator.validate_match_update(match_data)
                    logger.info("✓ Schema validation passed")
                    
                    # Check required fields
                    required_fields = [
                        "idEvent", "strEvent", "strLeague", "strHomeTeam",
                        "strAwayTeam", "dateEvent", "strTime", "strStatus"
                    ]
                    for field in required_fields:
                        assert field in match_data, f"Missing required field: {field}"
                    logger.info("✓ All required fields present")
                    
                    # Check status
                    valid_statuses = ["Not Started", "Live", "Finished", "Postponed", "Cancelled"]
                    assert match_data["strStatus"] in valid_statuses, f"Invalid status: {match_data['strStatus']}"
                    logger.info(f"✓ Valid status: {match_data['strStatus']}")
                    
                    # Check scores
                    if match_data["intHomeScore"] is not None:
                        assert isinstance(match_data["intHomeScore"], int), "Home score must be integer"
                    if match_data["intAwayScore"] is not None:
                        assert isinstance(match_data["intAwayScore"], int), "Away score must be integer"
                    logger.info("✓ Score types valid")
                    
                    # Check odds
                    assert "odds" in match_data, "Missing odds"
                    assert all(k in match_data["odds"] for k in ["home_win", "draw", "away_win"]), "Missing odds fields"
                    assert all(isinstance(v, (int, float)) for v in match_data["odds"].values()), "Invalid odds values"
                    print("✓ Odds structure valid")
                    
                    # Print formatted data
                    print("\nFormatted match data:")
                    print(json.dumps(match_data, indent=2))
                    
                except Exception as e:
                    print(f"✗ Validation failed: {str(e)}")
                    print("\nInvalid match data:")
                    print(json.dumps(match_data, indent=2))
                    
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_match_formatting()) 