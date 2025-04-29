"""Kafka producer service."""
import json
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaProducer
from src.config import settings

logger = logging.getLogger(__name__)

# Global producer instance
producer = None


async def get_producer() -> AIOKafkaProducer:
    """Get or create Kafka producer instance.
    
    Returns:
        AIOKafkaProducer instance
    """
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        logger.info("Kafka producer initialized")
    return producer


async def produce_message(topic: str, value: Dict[str, Any]) -> None:
    """Produce message to Kafka topic.
    
    Args:
        topic: Kafka topic name
        value: Message value to produce
        
    Raises:
        RuntimeError: If producer fails to send message
    """
    try:
        producer = await get_producer()
        await producer.send_and_wait(topic, value)
        logger.debug(f"Produced message to topic {topic}")
    except Exception as e:
        logger.error(f"Failed to produce message: {str(e)}")
        raise RuntimeError(f"Failed to produce message: {str(e)}")


async def cleanup() -> None:
    """Cleanup Kafka producer resources."""
    global producer
    if producer is not None:
        await producer.stop()
        producer = None
        logger.info("Kafka producer stopped") 