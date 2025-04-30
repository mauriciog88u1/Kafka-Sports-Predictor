"""Kafka consumer for match data processing."""
import asyncio
import json
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from src.config import settings
from src.database import get_db
import sqlalchemy as sa

logger = logging.getLogger(__name__)

async def calculate_odds(match_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate odds based on match data.
    
    Args:
        match_data: Raw match data from Kafka
        
    Returns:
        Dictionary containing calculated odds
    """
    # Get team stats from last 5 matches
    home_stats = await get_team_stats(match_data["idHomeTeam"])
    away_stats = await get_team_stats(match_data["idAwayTeam"])
    
    # Calculate basic probabilities
    home_strength = (home_stats.get("goals_scored_last_5", 0) + 1) / (home_stats.get("goals_conceded_last_5", 0) + 1)
    away_strength = (away_stats.get("goals_scored_last_5", 0) + 1) / (away_stats.get("goals_conceded_last_5", 0) + 1)
    
    # Apply home advantage
    home_strength *= 1.1
    
    # Calculate probabilities
    total = home_strength + away_strength + 1
    home_prob = home_strength / total
    away_prob = away_strength / total
    draw_prob = 1 - (home_prob + away_prob)
    
    # Convert to odds with margin
    margin = 1.07  # 7% margin
    return {
        "home": round(1 / (home_prob / margin), 2),
        "draw": round(1 / (draw_prob / margin), 2),
        "away": round(1 / (away_prob / margin), 2)
    }

async def get_team_stats(team_id: str) -> Dict[str, Any]:
    """Get team statistics from recent matches.
    
    Args:
        team_id: The ID of the team
        
    Returns:
        Dictionary containing team statistics
    """
    async with get_db() as db:
        query = sa.text(
            """
            SELECT 
                SUM(CASE WHEN idHomeTeam = :team_id THEN intHomeScore ELSE intAwayScore END) as goals_scored_last_5,
                SUM(CASE WHEN idHomeTeam = :team_id THEN intAwayScore ELSE intHomeScore END) as goals_conceded_last_5
            FROM (
                SELECT * FROM matches 
                WHERE idHomeTeam = :team_id OR idAwayTeam = :team_id
                ORDER BY dateEvent DESC 
                LIMIT 5
            ) as recent_matches
            """
        )
        result = await db.execute(query, {"team_id": team_id})
        row = result.first()
        
        if row is None:
            return {"goals_scored_last_5": 0, "goals_conceded_last_5": 0}
            
        return {
            "goals_scored_last_5": row.goals_scored_last_5 or 0,
            "goals_conceded_last_5": row.goals_conceded_last_5 or 0
        }

async def store_prediction(match_id: str, odds: Dict[str, float]) -> None:
    """Store prediction in database.
    
    Args:
        match_id: The ID of the match
        odds: Calculated odds
    """
    async with get_db() as db:
        query = sa.text(
            """
            INSERT INTO predictions 
            (match_id, home_win_prob, draw_prob, away_win_prob, confidence, 
             model_version, expected_goals_home, expected_goals_away, key_factors, timestamp)
            VALUES 
            (:match_id, :home_prob, :draw_prob, :away_prob, :confidence,
             :model_version, :expected_goals_home, :expected_goals_away, :key_factors, NOW())
            ON DUPLICATE KEY UPDATE
            home_win_prob = :home_prob,
            draw_prob = :draw_prob,
            away_win_prob = :away_prob,
            confidence = :confidence,
            model_version = :model_version,
            expected_goals_home = :expected_goals_home,
            expected_goals_away = :expected_goals_away,
            key_factors = :key_factors,
            timestamp = NOW()
            """
        )
        await db.execute(
            query,
            {
                "match_id": match_id,
                "home_prob": 1 / odds["home"],
                "draw_prob": 1 / odds["draw"],
                "away_prob": 1 / odds["away"],
                "confidence": 0.85,  # Default confidence
                "model_version": "1.0.0",  # Default version
                "expected_goals_home": 1.8,  # Default xG
                "expected_goals_away": 1.2,  # Default xG
                "key_factors": json.dumps([
                    "Home team recent form",
                    "Head to head record"
                ])
            }
        )
        await db.commit()

async def consume_matches():
    """Consume match data from Kafka and process it."""
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP,
        group_id=settings.KAFKA_GROUP_ID,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
        sasl_plain_username=settings.KAFKA_USERNAME,
        sasl_plain_password=settings.KAFKA_PASSWORD,
        auto_offset_reset=settings.KAFKA_CONSUMER_AUTO_OFFSET_RESET,
        enable_auto_commit=settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT,
        max_poll_records=settings.KAFKA_CONSUMER_MAX_POLL_RECORDS,
        session_timeout_ms=settings.KAFKA_CONSUMER_SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=settings.KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS
    )
    
    try:
        await consumer.start()
        logger.info("Kafka consumer started")
        
        async for msg in consumer:
            try:
                match_data = msg.value
                logger.info(f"Processing match: {match_data['strEvent']}")
                
                # Calculate odds
                odds = await calculate_odds(match_data)
                logger.info(f"Calculated odds: {odds}")
                
                # Store prediction
                await store_prediction(match_data["idEvent"], odds)
                logger.info(f"Stored prediction for match {match_data['idEvent']}")
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped") 