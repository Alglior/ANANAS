# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*
RUN groupadd -r appuser && useradd -r -g appuser -m -s /bin/bash appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ln -sf alembic migrations \
    && chown -R appuser:appuser /app

USER appuser

ENV FLASK_ENV=production

EXPOSE 5000

CMD ["sh", "/app/docker-entrypoint.sh"]
