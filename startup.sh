#!/bin/bash

echo "Starting SaaS API..."

sleep 5

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start application
echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
