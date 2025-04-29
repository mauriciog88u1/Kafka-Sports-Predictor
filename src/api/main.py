"""Main FastAPI application."""
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.api.services import sports_db, kafka, predictions
from src.utils.validation import SchemaValidator

logger = logging.getLogger(__name__)

app = FastAPI(title="Sports Prediction API")
validator = SchemaValidator()


class MatchBatchRequest(BaseModel):
    """Request model for batch match processing."""
    match_ids: List[str] = Field(..., min_items=1)


class MatchBatchResponse(BaseModel):
    """Response model for batch match processing."""
    status: str
    processed: int
    errors: List[Dict[str, Any]] = []


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
    
    processed = 0
    errors = []
    
    for match_id in request.match_ids:
        try:
            # Get match data (which includes calculated odds)
            match_data = await sports_db.get_match_data(match_id)
            
            # Validate data
            try:
                validator.validate_match_update(match_data)
            except Exception as e:
                logger.error(f"Validation error for match {match_id}: {str(e)}")
                raise HTTPException(
                    status_code=422,
                    detail=f"Validation error: {str(e)}"
                )
            
            # Produce to Kafka
            await kafka.produce_message(
                topic="match_updates",
                value=match_data
            )
            
            processed += 1
            
        except ValueError as e:
            errors.append({
                "match_id": match_id,
                "error": str(e)
            })
        except Exception as e:
            logger.error(f"Error processing match {match_id}: {str(e)}")
            errors.append({
                "match_id": match_id,
                "error": "Internal server error"
            })
    
    if processed == 0 and errors:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "All matches failed to process",
                "details": errors
            }
        )
    
    return MatchBatchResponse(
        status="success",
        processed=processed,
        errors=errors
    )


@app.get("/api/v1/predictions/{match_id}")
async def get_prediction(match_id: str) -> Dict[str, Any]:
    """Get prediction for a specific match.
    
    Args:
        match_id: Match identifier
        
    Returns:
        Prediction data
        
    Raises:
        HTTPException: If prediction not found
    """
    try:
        prediction = await predictions.get_prediction_from_db(match_id)
        if not prediction:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction found for match {match_id}"
            )
        return prediction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction for match {match_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await kafka.cleanup() 