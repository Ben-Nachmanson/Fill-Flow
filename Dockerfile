# Multi-stage Dockerfile for the trade-svc
FROM python:3.10-slim AS builder
WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.10-slim
WORKDIR /app

# Create non-root user and ensure /app exists
RUN useradd -m appuser || true \
    && mkdir -p /app \
    && chown -R appuser:appuser /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy source
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "internal.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
