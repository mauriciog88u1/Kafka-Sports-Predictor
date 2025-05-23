"""Predictions service for database operations."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import sqlalchemy as sa
from src.config import settings
from src.database import get_db

logger = logging.getLogger(__name__)


async def get_prediction_from_db(match_id: str) -> Optional[Dict[str, Any]]:
    """Get prediction for a match from the database.
    
    Args:
        match_id: The ID of the match
        
    Returns:
        Prediction data if found, None otherwise
        
    Raises:
        Exception: If database error occurs
    """
    try:
        async with get_db() as db:
            query = sa.text(
                """
                SELECT * FROM predictions 
                WHERE match_id = :match_id 
                ORDER BY timestamp DESC 
                LIMIT 1
                """
            )
            result = await db.execute(query, {"match_id": match_id})
            row = result.first()
            
            if row is None:
                return None
                
            return {
                "match_id": row.match_id,
                "home_win_prob": float(row.home_win_prob),
                "draw_prob": float(row.draw_prob),
                "away_win_prob": float(row.away_win_prob),
                "confidence": float(row.confidence) if hasattr(row, 'confidence') else 0.85,  # Default confidence
                "timestamp": row.timestamp.isoformat(),
                "model_version": getattr(row, 'model_version', '1.0.0'),  # Default version
                "additional_info": {
                    "expected_goals_home": float(getattr(row, 'expected_goals_home', 1.8)),  # Default xG
                    "expected_goals_away": float(getattr(row, 'expected_goals_away', 1.2)),  # Default xG
                    "key_factors": getattr(row, 'key_factors', []) or [
                        "Home team recent form",
                        "Head to head record"
                    ]
                }
            }
            
    except Exception as e:
        logger.error(f"Error fetching prediction for match {match_id}: {str(e)}")
        raise 