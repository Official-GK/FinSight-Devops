"""
Risk Engine - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RiskCalculationRequest(BaseModel):
    """Payload received from the Analytics API."""
    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    transaction_amount: float = Field(..., gt=0, description="Transaction amount in USD")
    transaction_type: str = Field(..., description="Type of transaction")
    currency: str = Field(default="USD", description="ISO 4217 currency code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "transaction_id": "txn-abc-123",
                "transaction_amount": 15000.50,
                "transaction_type": "TRADE",
                "currency": "USD",
            }
        }
    }


class RiskCalculationResponse(BaseModel):
    """Structured risk score payload returned to the Analytics API."""
    transaction_id: str
    risk_score: float = Field(..., description="Calculated risk score (0.0 to 100.0+)")
    raw_score: float = Field(..., description="Raw pre-normalized score")
    market_volatility_factor: float = Field(..., description="Volatility factor used")
    transaction_type: str
    transaction_amount: float
    computation_time_ms: float
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
