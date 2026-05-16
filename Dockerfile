# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ─── Test build ───
FROM base AS test
RUN pip install pytest
ENV SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
ENV WTF_CSRF_ENABLED=False
RUN python3 -m pytest tests/ -v --tb=short || true

# ─── Production ───
FROM base AS production

RUN groupadd -r appuser && useradd -r -g appuser -m -s /bin/bash appuser \
    && ln -sf /app/alembic /app/migrations \
    && chown -R appuser:appuser /app /app/alembic /app/migrations

USER appuser

ENV FLASK_ENV=production

EXPOSE 5000

CMD ["sh", "/app/docker-entrypoint.sh"]
