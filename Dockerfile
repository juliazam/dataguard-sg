# Stage 1 — build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --target=/app/deps ".[dev]"

# Stage 2 — final image
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/deps /app/deps
ENV PYTHONPATH=/app/deps:/app/src

COPY config.yaml .
COPY pyproject.toml .
COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

CMD ["python", "src/dataguard/main.py"]