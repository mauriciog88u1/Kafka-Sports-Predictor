"""Kafka consumer for match data processing."""
import asyncio
import json
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from src.config import settings

logger = logging.getLogger(__name__)

async def calculate_odds(match_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate odds based on match data.
    
    Args:
        match_data: Raw match data from Kafka
        
    Returns:
        Dictionary containing calculated odds
    """
    # Get team stats from match data
    home_stats = match_data["team_stats"]["home"]
    away_stats = match_data["team_stats"]["away"]
    
    # Calculate basic probabilities
    home_strength = (
        (home_stats["form"]["form_score"] / 100) * 0.3 +  # Form weight
        (home_stats["avg_goals_scored"] / (home_stats["avg_goals_conceded"] + 0.1)) * 0.3 +  # Goals ratio weight
        (home_stats["xg_for"] / (home_stats["xg_against"] + 0.1)) * 0.4  # xG ratio weight
    )
    
    away_strength = (
        (away_stats["form"]["form_score"] / 100) * 0.3 +  # Form weight
        (away_stats["avg_goals_scored"] / (away_stats["avg_goals_conceded"] + 0.1)) * 0.3 +  # Goals ratio weight
        (away_stats["xg_for"] / (away_stats["xg_against"] + 0.1)) * 0.4  # xG ratio weight
    )
    
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

async def calculate_prediction(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate match prediction based on team stats and form.
    
    Args:
        match_data: Raw match data from Kafka
        
    Returns:
        Dictionary containing match prediction
    """
    # Get team stats
    home_stats = match_data["team_stats"]["home"]
    away_stats = match_data["team_stats"]["away"]
    
    # Calculate team strengths
    home_strength = (
        (home_stats["form"]["form_score"] / 100) * 0.4 +  # Form weight
        (home_stats["avg_goals_scored"] / (home_stats["avg_goals_conceded"] + 0.1)) * 0.3 +  # Goals ratio weight
        (home_stats["xg_for"] / (home_stats["xg_against"] + 0.1)) * 0.3  # xG ratio weight
    )
    
    away_strength = (
        (away_stats["form"]["form_score"] / 100) * 0.4 +  # Form weight
        (away_stats["avg_goals_scored"] / (away_stats["avg_goals_conceded"] + 0.1)) * 0.3 +  # Goals ratio weight
        (away_stats["xg_for"] / (away_stats["xg_against"] + 0.1)) * 0.3  # xG ratio weight
    )
    
    # Apply home advantage
    home_strength *= 1.1
    
    # Calculate expected goals
    home_xg = (home_stats["xg_for"] + away_stats["xg_against"]) / 2
    away_xg = (away_stats["xg_for"] + home_stats["xg_against"]) / 2
    
    # Calculate probabilities
    total = home_strength + away_strength + 1
    home_prob = home_strength / total
    away_prob = away_strength / total
    draw_prob = 1 - (home_prob + away_prob)
    
    # Determine most likely outcome
    if home_prob > away_prob and home_prob > draw_prob:
        predicted_outcome = "home_win"
    elif away_prob > home_prob and away_prob > draw_prob:
        predicted_outcome = "away_win"
    else:
        predicted_outcome = "draw"
    
    # Calculate confidence score
    confidence = max(home_prob, away_prob, draw_prob)
    
    return {
        "match_id": match_data["idEvent"],
        "predicted_outcome": predicted_outcome,
        "confidence": round(confidence * 100, 1),
        "expected_goals": {
            "home": round(home_xg, 2),
            "away": round(away_xg, 2)
        },
        "probabilities": {
            "home_win": round(home_prob * 100, 1),
            "draw": round(draw_prob * 100, 1),
            "away_win": round(away_prob * 100, 1)
        }
    }

async def consume_matches(consumer: AIOKafkaConsumer) -> None:
    """Consume match data from Kafka and calculate predictions.
    
    Args:
        consumer: Kafka consumer instance
    """
    try:
        async for msg in consumer:
            try:
                # Log message receipt
                logger.info(f"Received match data from partition {msg.partition} at offset {msg.offset}")
                logger.debug(f"Raw message: {msg.value}")
                
                # Deserialize message
                try:
                    match_data = json.loads(msg.value) if isinstance(msg.value, str) else msg.value
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {str(e)}")
                    logger.error(f"Raw message: {msg.value}")
                    continue
                    
                # Validate message format
                if not isinstance(match_data, dict):
                    logger.error(f"Invalid message format: {type(match_data)}")
                    logger.error(f"Message content: {match_data}")
                    continue
                    
                # Validate required fields
                required_fields = ['idEvent', 'team_stats']
                missing_fields = [field for field in required_fields if field not in match_data]
                if missing_fields:
                    logger.error(f"Missing required fields: {missing_fields}")
                    logger.error(f"Match data: {match_data}")
                    continue
                    
                # Validate team stats structure
                if not isinstance(match_data['team_stats'], dict) or 'home' not in match_data['team_stats'] or 'away' not in match_data['team_stats']:
                    logger.error("Invalid team stats structure")
                    logger.error(f"Team stats: {match_data['team_stats']}")
                    continue
                    
                # Calculate prediction
                try:
                    prediction = await calculate_prediction(match_data)
                    logger.info(f"Calculated prediction for match {match_data['idEvent']}: {prediction}")
                    
                    # Send prediction to output topic
                    await send_prediction(prediction)
                    
                except Exception as e:
                    logger.error(f"Error calculating prediction: {str(e)}")
                    logger.error(f"Match data: {match_data}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                logger.error(f"Message content: {msg.value}")
                
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
    finally:
        await consumer.stop()
        logger.info("Match consumer stopped")

async def send_prediction(prediction: Dict[str, Any]) -> None:
    """Send calculated prediction to output topic.
    
    Args:
        prediction: Dictionary of calculated prediction
    """
    try:
        producer = await get_producer()
        await producer.send(settings.KAFKA_TOPIC, prediction)
        logger.info(f"Sent prediction to topic {settings.KAFKA_TOPIC}")
    except Exception as e:
        logger.error(f"Error sending prediction: {str(e)}")
        raise

async def send_odds(odds: Dict[str, float]) -> None:
    """Send calculated odds to output topic.
    
    Args:
        odds: Dictionary of calculated odds
    """
    try:
        producer = await get_producer()
        await producer.send(
            settings.KAFKA_OUTPUT_TOPIC,
            value=json.dumps(odds).encode('utf-8')
        )
        logger.info(f"Sent odds to output topic: {odds}")
    except Exception as e:
        logger.error(f"Error sending odds: {str(e)}") 