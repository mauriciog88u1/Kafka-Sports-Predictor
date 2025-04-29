"""Logging configuration."""
import logging
import sys
from src.config import settings

def setup_logging():
    """Setup logging configuration."""
    # Create formatters
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    info_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(debug_formatter)
    
    # Create file handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(debug_formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set specific loggers to DEBUG
    logging.getLogger('src.api.services.kafka').setLevel(logging.DEBUG)
    logging.getLogger('src.api.services.sports_db').setLevel(logging.DEBUG)
    logging.getLogger('src.api.main').setLevel(logging.DEBUG)
    
    logging.info("Logging configuration completed") 