#!/bin/sh

# Create data directory if it doesn't exist
mkdir -p /app/data

# Run database migrations
alembic upgrade head

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
