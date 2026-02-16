#!/bin/bash

echo " Starting SaaS API..."

# Wait for database to be ready
sleep 5

# Create tables if they don't exist
echo " Creating database tables..."
python init_db.py || echo " Tables may already exist"

# Start application
echo "✅ Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
