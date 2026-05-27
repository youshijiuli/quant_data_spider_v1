# ===== Build stage =====
FROM python:3.10-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml .
RUN pip wheel --no-cache-dir --wheel-dir=/build/wheels -e ".[dev]" 2>/dev/null || \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels \
        akshare apscheduler typer rich tomli pandas numpy \
        sqlalchemy pymysql loguru pydantic pydantic-settings \
        python-dotenv alembic fastapi uvicorn httpx

# ===== Runtime stage =====
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash quant

WORKDIR /app

COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

COPY --chown=quant:quant . .

RUN mkdir -p /app/logs && chown -R quant:quant /app/logs /app/config

USER quant

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "scripts/run_web.py"]
