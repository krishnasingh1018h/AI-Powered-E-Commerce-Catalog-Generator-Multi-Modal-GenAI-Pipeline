#!/bin/bash
# Start script for production deployment (Render, Docker, Railway, local)
PORT="${PORT:-8000}"
echo "Starting CatalogStream AI FastAPI Server on port $PORT..."
exec uvicorn model.api:app --host 0.0.0.0 --port "$PORT"