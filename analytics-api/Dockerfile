# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# Install dependencies into an isolated virtualenv using a full Python image.
# This keeps build tools out of the final production image.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Prevent .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install system deps required by some Python packages (e.g., httpx, uvloop)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer cache
COPY requirements.txt .

# Create virtualenv and install all dependencies into it
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Production Runtime
# Minimal distroless-style image — no build tools, no package managers.
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point Python to the venv from the builder stage
    PATH="/opt/venv/bin:$PATH" \
    # Application defaults (overridden by K8s ConfigMap / env vars)
    APP_NAME="analytics-api" \
    APP_VERSION="1.0.0" \
    ENVIRONMENT="production" \
    HOST="0.0.0.0" \
    PORT="8000" \
    WORKERS="1" \
    LOG_LEVEL="INFO" \
    RISK_ENGINE_URL="http://risk-engine-service:8001"

# Security: create a non-root user to run the application
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy virtualenv from builder (no pip / build tools in this layer)
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY --chown=appuser:appgroup app/ ./app/

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Expose Prometheus metrics port (scraped by Prometheus via ServiceMonitor)
EXPOSE 9090

# Health check using the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start with uvicorn using uvloop for maximum async performance
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--log-level", "warning", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
