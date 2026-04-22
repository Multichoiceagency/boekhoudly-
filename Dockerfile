FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-nld \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

# Run `alembic upgrade head` before booting uvicorn so schema changes land
# before any endpoint is served. The entrypoint exec's uvicorn so it becomes
# PID 1 and signals/graceful shutdown still work.
ENTRYPOINT ["/app/docker-entrypoint.sh"]
