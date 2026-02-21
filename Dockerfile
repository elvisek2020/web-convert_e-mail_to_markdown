FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY static/ ./static/

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/output /tmp/transcendence_emails \
    && chown -R appuser:appuser /app /tmp/transcendence_emails

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
