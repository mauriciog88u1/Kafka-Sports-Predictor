"""Common test fixtures."""
import pytest
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Import after setting up path
from src.database import get_db


@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for testing."""
    test_env = {
        # SportsDB API settings
        "SPORTSDB_API_KEY": "638861",
        "SPORTSDB_BASE_URL": "https://www.thesportsdb.com/api/v1/json",

        # Application settings
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "PORT": "8000",

        # Database settings (using SQLite for testing)
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "DB_PRIVATE_IP": "True",
        "DB_SSL_MODE": "verify-ca",

        # Kafka settings
        "KAFKA_BOOTSTRAP": "localhost:9092",
        "KAFKA_SECURITY_PROTOCOL": "PLAINTEXT",
        "KAFKA_SASL_MECHANISM": "PLAIN",
        "KAFKA_USERNAME": "test_user",
        "KAFKA_PASSWORD": "test_password",
        "KAFKA_GROUP_ID": "test-group",
        "KAFKA_TOPIC": "test-topic",

        # Kafka Producer settings
        "KAFKA_PRODUCER_ACKS": "all",
        "KAFKA_PRODUCER_RETRIES": "3",
        "KAFKA_PRODUCER_BATCH_SIZE": "16384",
        "KAFKA_PRODUCER_LINGER_MS": "1",
        "KAFKA_PRODUCER_BUFFER_MEMORY": "33554432",

        # Kafka Consumer settings
        "KAFKA_CONSUMER_AUTO_OFFSET_RESET": "latest",
        "KAFKA_CONSUMER_ENABLE_AUTO_COMMIT": "false",
        "KAFKA_CONSUMER_MAX_POLL_RECORDS": "500",
        "KAFKA_CONSUMER_SESSION_TIMEOUT_MS": "45000",
        "KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS": "15000"
    }
    
    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value
        
    yield
    
    # Clean up environment variables
    for key in test_env:
        os.environ.pop(key, None)


@pytest.fixture
def test_db():
    """Create a test database."""
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    from src.models.base import Base
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    return override_get_db 