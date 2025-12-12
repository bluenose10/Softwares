#!/bin/bash
# Startup script for Railway deployment

# Use Railway's PORT variable, or default to 8000
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
