"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "Maintenance Module"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vending_user:vending_pass@localhost:5432/vending",
        description="Async PostgreSQL connection URL",
    )
    DB_ECHO: bool = False
    DB_POOL_DISABLED: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Telegram Bot
    BOT_TOKEN: str = ""
    BOT_WEBHOOK_URL: Optional[str] = None

    # S3 Storage
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "vending-photos"
    S3_REGION: str = "us-east-1"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin API (for initial setup - replace with proper auth)
    ADMIN_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()