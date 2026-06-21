from fastapi import APIRouter
from app.models import DashboardSummaryResponse, DashboardAnalyticsResponse
from app.in_memory_db import db

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary():
    with db.lock:
        avg_risk = db.total_risk_score / db.total_transactions if db.total_transactions > 0 else 0.0
        
        # Calculate market volatility index (mock metric based on RPS and high risk ratio)
        high_risk_ratio = db.high_risk_transactions / db.total_transactions if db.total_transactions > 0 else 0
        volatility = min(100.0, (db.rps * 0.5) + (high_risk_ratio * 100 * 0.5))
        
        return DashboardSummaryResponse(
            total_transactions=db.total_transactions,
            average_risk_score=round(avg_risk, 2),
            high_risk_transactions=db.high_risk_transactions,
            requests_per_second=round(db.rps, 1),
            market_volatility_index=round(volatility, 1)
        )

@router.get("/analytics", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics():
    with db.lock:
        return DashboardAnalyticsResponse(
            risk_distribution=dict(db.risk_distribution),
            recent_transactions=list(db.recent_transactions),
            transactions_over_time=list(db.transactions_over_time),
            risk_trend=list(db.risk_trend)
        )

@router.get("/transactions")
async def get_dashboard_transactions():
    with db.lock:
        return {"transactions": list(db.recent_transactions)}
