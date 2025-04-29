"""Kafka producer and consumer service."""
import json
import logging
import ssl
import asyncio
from typing import Dict, Any, Callable
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from src.config import settings

logger = logging.getLogger(__name__)

# Global producer and consumer instances
producer = None
consumer = None

# Message handler type
MessageHandler = Callable[[Dict[str, Any]], None]

async def get_producer() -> AIOKafkaProducer:
    """Get or create Kafka producer instance.
    
    Returns:
        AIOKafkaProducer instance
    """
    global producer
    if producer is None:
        # Create SSL context for SASL_SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
            ssl_context=ssl_context
        )
        await producer.start()
        logger.info("Kafka producer initialized")
    return producer

async def get_consumer(handler: MessageHandler) -> AIOKafkaConsumer:
    """Get or create Kafka consumer instance.
    
    Args:
        handler: Function to handle incoming messages
        
    Returns:
        AIOKafkaConsumer instance
    """
    global consumer
    if consumer is None:
        # Create SSL context for SASL_SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP,
            group_id=settings.KAFKA_GROUP_ID,
            auto_offset_reset=settings.KAFKA_CONSUMER_AUTO_OFFSET_RESET,
            enable_auto_commit=settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT,
            max_poll_records=settings.KAFKA_CONSUMER_MAX_POLL_RECORDS,
            session_timeout_ms=settings.KAFKA_CONSUMER_SESSION_TIMEOUT_MS,
            heartbeat_interval_ms=settings.KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS,
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
            ssl_context=ssl_context
        )
        await consumer.start()
        logger.info("Kafka consumer initialized")
        
        # Start consuming messages in the background
        asyncio.create_task(consume_messages(consumer, handler))
        
    return consumer

async def consume_messages(consumer: AIOKafkaConsumer, handler: MessageHandler) -> None:
    """Consume messages from Kafka topic.
    
    Args:
        consumer: Kafka consumer instance
        handler: Function to handle incoming messages
    """
    try:
        async for msg in consumer:
            try:
                # Decode message
                message_data = json.loads(msg.value.decode())
                logger.debug(f"Received message: {json.dumps(message_data, indent=2)}")
                
                # Handle message
                handler(message_data)
                
                # Commit offset if auto commit is disabled
                if not settings.KAFKA_CONSUMER_ENABLE_AUTO_COMMIT:
                    await consumer.commit()
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {str(e)}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")

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
        # Add detailed debug logging
        logger.debug(f"Producing message to topic '{topic}':")
        logger.debug(f"Message content: {json.dumps(value, indent=2)}")
        logger.debug(f"Message size: {len(json.dumps(value))} bytes")
        
        await producer.send_and_wait(topic, value)
        logger.debug(f"Successfully produced message to topic {topic}")
    except Exception as e:
        logger.error(f"Failed to produce message: {str(e)}")
        logger.error(f"Failed message content: {json.dumps(value, indent=2)}")
        raise RuntimeError(f"Failed to produce message: {str(e)}")

async def cleanup() -> None:
    """Cleanup Kafka producer and consumer resources."""
    global producer, consumer
    if producer is not None:
        await producer.stop()
        producer = None
        logger.info("Kafka producer stopped")
    if consumer is not None:
        await consumer.stop()
        consumer = None
        logger.info("Kafka consumer stopped") 