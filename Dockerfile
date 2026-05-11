# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser -m -s /bin/bash appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app \
    && chmod 755 /app

USER appuser

ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "3", "--timeout", "30", "app:create_app()"]
