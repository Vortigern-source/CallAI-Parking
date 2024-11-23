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

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

# Keep container alive
echo "Keeping container alive..."
wait
