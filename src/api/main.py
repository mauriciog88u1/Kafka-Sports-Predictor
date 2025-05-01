"""Main FastAPI application."""
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from src.api.services import sports_db, kafka
from src.utils.validation import SchemaValidator
from src.config import settings
from src.utils.logging import setup_logging
import json
import random

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Sports Prediction API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://24.1.229.192",
        "https://24.1.229.192",
        "http://mauric10.com",
        "https://mauric10.com",
        "https://bet365-predictor-api-806378004153.us-central1.run.app",
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)

# Add OPTIONS handler for preflight requests
@app.options("/api/v1/matches/batch")
async def preflight_handler():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://mauric10.com",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "600"
        }
    )

validator = SchemaValidator()


class MatchBatchRequest(BaseModel):
    """Request model for batch match processing."""
    match_ids: List[str] = Field(..., min_items=1)


class MatchBatchResponse(BaseModel):
    """Response model for batch match processing."""
    status: str = Field(..., description="Status of the processing operation")
    processed: int = Field(..., description="Number of matches successfully processed")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="List of errors encountered")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="List of processed match data")


async def handle_prediction_message(message: Dict[str, Any]) -> None:
    """Handle incoming prediction messages from Kafka.
    
    Args:
        message: The prediction message to handle
    """
    try:
        logger.info("=== Received Kafka Message ===")
        logger.info(f"Message type: {type(message)}")
        logger.info(f"Message content: {json.dumps(message, indent=2)}")
        
        # Extract key match data for logging
        match_id = message.get('idEvent')
        home_team = message.get('strHomeTeam')
        away_team = message.get('strAwayTeam')
        logger.info(f"Processing match: {home_team} vs {away_team} (ID: {match_id})")
        
        # Log team stats
        team_stats = message.get('team_stats', {})
        if team_stats:
            home_stats = team_stats.get('home', {})
            away_stats = team_stats.get('away', {})
            logger.info(f"Home team form score: {home_stats.get('form', {}).get('form_score')}")
            logger.info(f"Away team form score: {away_stats.get('form', {}).get('form_score')}")
        
        # Log odds
        odds = message.get('odds', {})
        if odds:
            logger.info(f"Match odds - Home: {odds.get('home_win')}, Draw: {odds.get('draw')}, Away: {odds.get('away_win')}")
        
        logger.info("=== End of Message Processing ===")
        
    except Exception as e:
        logger.error(f"Error handling prediction message: {str(e)}")
        logger.error(f"Failed message content: {json.dumps(message, indent=2)}")
        raise


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    # Initialize Kafka consumer
    await kafka.get_consumer(handler=handle_prediction_message)
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await kafka.cleanup()
    logger.info("Application shutdown completed")


@app.post("/api/v1/matches/batch", response_model=MatchBatchResponse)
async def process_match_batch(request: MatchBatchRequest) -> MatchBatchResponse:
    """Process a batch of match IDs.
    
    Args:
        request: Request containing list of match IDs
        
    Returns:
        Response with processing status and results
        
    Raises:
        HTTPException: If processing fails
    """
    # Check for duplicate IDs
    if len(set(request.match_ids)) != len(request.match_ids):
        raise HTTPException(
            status_code=400,
            detail="Duplicate match IDs in request"
        )
    
    try:
        # Process matches in batches with rate limiting
        results, errors = await sports_db.process_match_batch(request.match_ids)
        
        return MatchBatchResponse(
            status="success",
            processed=len(results),
            errors=errors,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/predictions/{match_id}")
async def get_prediction(match_id: str) -> Dict[str, Any]:
    """Get prediction for a specific match.
    
    Args:
        match_id: ID of the match to get prediction for
        
    Returns:
        Dictionary containing match prediction
    """
    try:
        # Get match data from SportsDB
        match_data = await sports_db.get_match_data(match_id)
        if not match_data:
            raise HTTPException(status_code=404, detail="Match not found")
            
        # Calculate prediction
        prediction = await calculate_prediction(match_data)
        
        return {
            "match_id": match_id,
            "status": "success",
            "prediction": prediction
        }
        
    except Exception as e:
        logger.error(f"Error getting prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def calculate_prediction(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate match prediction based on team stats and form.
    
    Args:
        match_data: Dictionary containing match and team data
        
    Returns:
        Dictionary containing prediction details
    """
    try:
        # Get team stats
        home_stats = match_data.get('team_stats', {}).get('home', {})
        away_stats = match_data.get('team_stats', {}).get('away', {})
        
        # Calculate prediction based on form and stats
        home_form_score = home_stats.get('form', {}).get('form_score', 50)  # Default to 50 if no form
        away_form_score = away_stats.get('form', {}).get('form_score', 50)  # Default to 50 if no form
        
        # Add home advantage (typically around 5-15% in football)
        home_advantage = 8  # Reduced from 10% to 8%
        home_form_score = home_form_score * (1 + home_advantage/100)
        
        # Add uncertainty factor (no result should ever be 100% certain)
        uncertainty = 35  # Increased from 15% to 35% for more realistic probabilities
        
        # Calculate base probabilities
        total_score = home_form_score + away_form_score
        base_home_prob = home_form_score / total_score if total_score > 0 else 0.40  # Reduced home advantage in default case
        base_away_prob = away_form_score / total_score if total_score > 0 else 0.35
        base_draw_prob = 1 - (base_home_prob + base_away_prob)
        
        # Apply uncertainty to make probabilities more realistic
        # This ensures no probability is too close to 0 or 1
        home_win_prob = (base_home_prob * (100 - uncertainty) + uncertainty/3) / 100
        away_win_prob = (base_away_prob * (100 - uncertainty) + uncertainty/3) / 100
        draw_prob = (base_draw_prob * (100 - uncertainty) + uncertainty/3) / 100
        
        # Normalize probabilities to ensure they sum to 1
        total_prob = home_win_prob + away_win_prob + draw_prob
        home_win_prob = home_win_prob / total_prob
        away_win_prob = away_win_prob / total_prob
        draw_prob = draw_prob / total_prob
        
        # Calculate expected goals with some randomness
        base_home_xg = home_stats.get('xg_for', 1.5)
        base_away_xg = away_stats.get('xg_for', 1.2)  # Slightly lower for away team
        
        # Add small random variation to expected goals (±0.3)
        home_xg = base_home_xg + (random.random() * 0.6 - 0.3)
        away_xg = base_away_xg + (random.random() * 0.6 - 0.3)
        
        # Calculate BTTS probability based on expected goals
        btts_prob = min(0.85, max(0.15, (home_xg * away_xg) / 4))  # Normalized between 15% and 85%
        
        # Calculate confidence level based on data quality and uncertainty
        confidence_score = min(0.95, max(0.35, 1 - uncertainty/100))  # Between 35% and 95%
        confidence_level = "high" if confidence_score > 0.75 else "medium" if confidence_score > 0.5 else "low"
        
        return {
            "home_win_probability": round(home_win_prob, 2),
            "draw_probability": round(draw_prob, 2),
            "away_win_probability": round(away_win_prob, 2),
            "expected_goals": {
                "home": round(home_xg, 2),
                "away": round(away_xg, 2)
            },
            "btts_probability": round(btts_prob, 2),
            "predicted_score": f"{round(home_xg)}-{round(away_xg)}",
            "confidence": confidence_level
        }
        
    except Exception as e:
        logger.error(f"Error calculating prediction: {str(e)}")
        raise


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dict[str, str]: Health status
    """
    return {"status": "healthy"} 