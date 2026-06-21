"""
Analytics API - Main Application Entry Point
Production-grade FastAPI application with:
- Lifespan management (startup/shutdown hooks)
- Prometheus metrics endpoint
- Structured JSON logging
- Request timing middleware
- CORS configuration
- Global exception handlers
"""
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.risk_engine_client import get_http_client, close_http_client
from app.routers.transactions import router as transactions_router
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS
from app.models import HealthResponse
from app.database import connect_db, disconnect_db

# Configure logging before anything else
configure_logging()

settings = get_settings()
logger = get_logger(__name__)


# ── Lifespan Manager ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and graceful shutdown."""
    logger.info(
        "analytics_api_starting",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        risk_engine_url=settings.RISK_ENGINE_URL,
    )
    # Pre-warm the HTTP connection pool
    await get_http_client()
    logger.info("http_client_pool_ready")
    
    # Connect to PostgreSQL / SQLite
    await connect_db()

    yield  # Application is running

    logger.info("analytics_api_shutting_down")
    await disconnect_db()
    await close_http_client()
    logger.info("analytics_api_shutdown_complete")


# ── FastAPI Application ───────────────────────────────────────────────────────
app = FastAPI(
    title="Financial Risk Analytics API",
    description=(
        "Production-grade API for real-time financial transaction risk analysis. "
        "Forwards payloads to the Risk Engine and returns calculated risk scores."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this per environment via config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_instrumentation_middleware(request: Request, call_next):
    """
    Middleware that:
    1. Generates a unique request ID for distributed tracing
    2. Measures request duration
    3. Records Prometheus metrics
    4. Emits structured access logs
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    ACTIVE_REQUESTS.inc()
    start = time.perf_counter()

    try:
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            http_status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(duration * 1000, 2))
        return response

    except Exception as exc:
        duration = time.perf_counter() - start
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            http_status=500,
        ).inc()
        logger.error("request_failed", error=str(exc), duration_ms=round(duration * 1000, 2))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred. Please contact support.",
                "request_id": request_id,
            }
        )
    finally:
        ACTIVE_REQUESTS.dec()


from app.routers.transactions import router as transactions_router
from app.routers.dashboard import router as dashboard_router

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(transactions_router)
app.include_router(dashboard_router)


# ── Health & Observability Endpoints ─────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Operations"],
    summary="Health Check",
    description="Kubernetes liveness and readiness probe endpoint.",
)
async def health_check() -> HealthResponse:
    """
    Returns service health status.
    Used by Kubernetes liveness and readiness probes.
    """
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        dependencies={
            "risk_engine": settings.RISK_ENGINE_URL,
        },
    )


@app.get(
    "/metrics",
    tags=["Operations"],
    summary="Prometheus Metrics",
    description="Exposes Prometheus-compatible metrics for scraping.",
    include_in_schema=False,
)
async def metrics():
    """Prometheus metrics scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/", tags=["Operations"], include_in_schema=False)
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }


# ── Global Exception Handlers ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please contact support.",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        },
    )
