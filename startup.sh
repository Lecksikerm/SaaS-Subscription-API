#!/bin/bash

echo "🚀 Starting SaaS API..."
echo "📊 Database URL: ${DATABASE_URL:0:50}..."

# Wait a moment for database to be ready
sleep 3

# Run database migrations
echo "📊 Running migrations..."
alembic upgrade head

# Start application
echo "✅ Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
