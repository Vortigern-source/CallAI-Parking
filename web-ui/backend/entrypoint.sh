#!/bin/bash
set -e

# Print environment information
echo "Starting CallAI Parking Platform..."
echo "Python Version: $(python --version)"
echo "Deployment Environment: ${ENVIRONMENT:-development}"

# Ensure data directory exists
mkdir -p /app/backend/data
chmod 777 /app/backend/data

# Run database seeding
echo "Seeding initial database..."
python seed_database.py || echo "Database seeding failed"

# Initialize Alembic migrations if not exists
if [ ! -d "/app/backend/migrations" ]; then
    echo "Initializing Alembic migrations..."
    alembic init migrations || echo "Alembic initialization failed"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "No migrations found or migration failed"

# Start web UI backend
echo "Starting Web UI Backend..."
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend static server
echo "Serving frontend static files..."
cd /app/backend/frontend
python -m http.server 3000 &

# Keep container alive
echo "Keeping container alive..."
wait
