"""
Application Configuration
Manages environment variables and settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    APP_NAME: str = "TextSQL API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # API
    API_V1_PREFIX: str = "/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql://textsql:textsql@localhost:5432/textsql"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    API_KEY_PREFIX: str = "textsql_"
    API_KEY_LENGTH: int = 32

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None  # Primary provider
    ANTHROPIC_API_KEY: Optional[str] = None  # Optional fallback
    DEFAULT_AI_PROVIDER: str = "openai"  # openai or anthropic
    DEFAULT_AI_MODEL: str = "gpt-4o"  # gpt-4o, gpt-4-turbo, or claude-3-5-sonnet-20241022
    AI_TIMEOUT: int = 30  # seconds
    AI_MAX_RETRIES: int = 3

    # SQL Generation
    SQL_CONFIDENCE_THRESHOLD: float = 0.70
    SQL_MAX_EXAMPLES: int = 5
    SQL_DEFAULT_LIMIT: int = 1000

    # Schema
    SCHEMA_MAX_SIZE_MB: int = 10
    SCHEMA_ENRICHMENT_BATCH_SIZE: int = 20

    # Query
    QUERY_HISTORY_RETENTION_DAYS: int = 90
    QUERY_MAX_EXECUTION_TIME_MS: int = 30000

    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()