# ── Stage 1: Builder (Compile dependencies & install CPU-only PyTorch) ──
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install temporary build tools required for compiling C-extensions (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated virtual environment for clean multi-stage extraction
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 1. Pre-install CPU-only PyTorch wheel
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install remaining requirements with CPU wheel index available
COPY backend/requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /build/requirements.txt


# ── Stage 2: Production Runner (Lean runtime without compiler toolchains) ──
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/backend:/app"

WORKDIR /app

# Install only runtime shared libraries (libpq5 for PostgreSQL, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy Backend and AI codebases (FastAPI spawns AI subprocesses from ai/)
COPY backend/ /app/backend/
COPY ai/ /app/ai/

WORKDIR /app/backend

EXPOSE 8000

# Keep exact existing healthcheck
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
