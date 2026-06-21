"""
Analytics API - Configuration Module
Reads all settings from environment variables for 12-factor app compliance.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    APP_NAME: str = "analytics-api"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Risk Engine
    RISK_ENGINE_URL: str = "http://risk-engine-service:8001"
    RISK_ENGINE_TIMEOUT: float = 30.0
    RISK_ENGINE_MAX_RETRIES: int = 3
    RISK_ENGINE_RETRY_WAIT: float = 1.0

    # HTTP Client Connection Pool
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE: int = 20

    # Metrics
    METRICS_PORT: int = 9090

    # Request limits
    MAX_TRANSACTION_AMOUNT: float = 10_000_000.0
    MIN_TRANSACTION_AMOUNT: float = 0.01


@lru_cache()
def get_settings() -> Settings:
    return Settings()
