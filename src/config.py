"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # SportsDB API settings
    SPORTSDB_API_KEY: str
    SPORTSDB_BASE_URL: str = "https://www.thesportsdb.com/api/v1/json"
    SPORTS_API_KEY: str | None = None  # For backward compatibility
    SPORTS_API_URL: str | None = None  # For backward compatibility

    # Application settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000

    # TODO: Database settings will be added in future implementation
    # DB_HOST: str
    # DB_PORT: int = 3306
    # DB_NAME: str
    # DB_USER: str
    # DB_PASSWORD: str
    # DB_PRIVATE_IP: bool = True
    # DB_SSL_MODE: str = "verify-ca"

    # Kafka settings
    KAFKA_BOOTSTRAP: str
    KAFKA_SECURITY_PROTOCOL: str = "SASL_SSL"
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_USERNAME: str
    KAFKA_PASSWORD: str
    KAFKA_GROUP_ID: str = "bet365-predictor"
    KAFKA_TOPIC: str = "match_predictions"

    # Kafka Producer settings
    KAFKA_PRODUCER_ACKS: str = "all"
    KAFKA_PRODUCER_RETRIES: int = 3
    KAFKA_PRODUCER_BATCH_SIZE: int = 16384
    KAFKA_PRODUCER_LINGER_MS: int = 1
    KAFKA_PRODUCER_BUFFER_MEMORY: int = 33554432

    # Kafka Consumer settings
    KAFKA_CONSUMER_AUTO_OFFSET_RESET: str = "latest"
    KAFKA_CONSUMER_ENABLE_AUTO_COMMIT: bool = False
    KAFKA_CONSUMER_MAX_POLL_RECORDS: int = 500
    KAFKA_CONSUMER_SESSION_TIMEOUT_MS: int = 45000
    KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS: int = 15000

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"  # Allow extra fields in the environment
    )


settings = Settings() 