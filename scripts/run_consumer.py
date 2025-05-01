"""Run Kafka consumer."""
import asyncio
import logging
from src.api.consumers.match_consumer import consume_matches
from src.utils.logging import setup_logging

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting match consumer")
        asyncio.run(consume_matches())
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}") 