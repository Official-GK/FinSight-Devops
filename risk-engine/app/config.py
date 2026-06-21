"""
Risk Engine - Configuration Module
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    APP_NAME: str = "risk-engine"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    WORKERS: int = 4

    # Risk Calculation Parameters
    # Base volatility factor — in production this would be fetched from a
    # market-data feed or Vault-managed config. Here it is env-configurable.
    MARKET_VOLATILITY_FACTOR: float = 0.0035

    # Volatility bounds for simulated jitter (±N% around base factor)
    VOLATILITY_JITTER_PCT: float = 0.15

    # Score normalization cap (raw scores are divided by this for 0-100 scale)
    SCORE_NORMALIZATION_DIVISOR: float = 35_000.0

    # Amplifiers per transaction type
    TYPE_RISK_AMPLIFIERS: dict = {
        "TRADE": 1.8,
        "TRANSFER": 1.4,
        "WITHDRAWAL": 1.2,
        "PAYMENT": 1.0,
        "DEPOSIT": 0.8,
        "REFUND": 0.6,
    }

    # Metrics
    METRICS_PORT: int = 9091


@lru_cache()
def get_settings() -> Settings:
    return Settings()
