FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY . .

# Ensure data directory exists for persistent SQLite and knowledge documents
RUN mkdir -p /app/data /app/data/uploads /app/data/router

ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/federated_mesh.db
ENV ROUTER_MODEL_PATH=/app/data/router/intent_router.joblib
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
