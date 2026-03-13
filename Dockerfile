FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by pdfplumber / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached independently of source)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create the data directory for SQLite.
# On Render, mount a Persistent Disk at /app/data so the DB survives deploys.
RUN mkdir -p /app/data

# Render injects $PORT at runtime (defaults to 10000).
# We fall back to 8000 for local docker run.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
