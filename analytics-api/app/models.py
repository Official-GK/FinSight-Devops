"""
Analytics API - Pydantic Models
Request/Response schemas with strict validation for production safety.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid


class TransactionType(str, Enum):
    PAYMENT = "PAYMENT"
    TRANSFER = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    TRADE = "TRADE"
    REFUND = "REFUND"


class TransactionRequest(BaseModel):
    """Incoming transaction analysis payload."""
    transaction_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique transaction identifier (auto-generated if not provided)",
    )
    amount: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Transaction amount in USD. Must be positive and <= 10M",
    )
    transaction_type: TransactionType = Field(
        ..., description="Type of the financial transaction"
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code (3 characters)",
    )
    metadata: Optional[dict] = Field(
        default=None, description="Optional metadata key-value pairs"
    )

    @field_validator("currency")
    @classmethod
    def currency_must_be_uppercase(cls, v: str) -> str:
        return v.upper()

    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": 15000.50,
                "transaction_type": "TRADE",
                "currency": "USD",
                "metadata": {"account_id": "ACC-001", "region": "us-east-1"},
            }
        }
    }


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisResponse(BaseModel):
    """Structured response returned to the API consumer."""
    transaction_id: str
    risk_score: float = Field(..., description="Calculated risk score (0.0 - 100.0+)")
    risk_level: RiskLevel
    amount: float
    transaction_type: TransactionType
    currency: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    engine_latency_ms: float = Field(
        ..., description="Time taken by the Risk Engine in milliseconds"
    )
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: dict


class ErrorResponse(BaseModel):
    error: str
    detail: str
    transaction_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DashboardSummaryResponse(BaseModel):
    total_transactions: int
    average_risk_score: float
    high_risk_transactions: int
    requests_per_second: float
    market_volatility_index: float

class DashboardAnalyticsResponse(BaseModel):
    risk_distribution: dict[str, int]
    recent_transactions: list[AnalysisResponse]
    transactions_over_time: list[dict] # list of {time: str, value: int}
    risk_trend: list[dict] # list of {time: str, value: float}

