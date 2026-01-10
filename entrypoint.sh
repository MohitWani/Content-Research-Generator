#!/bin/bash
set -e

echo "Starting AI Research Agent..."

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h ${DATABASE_HOST:-postgres} -p ${DATABASE_PORT:-5432} -U ${DATABASE_USER:-postgres} -q 2>/dev/null; do
    sleep 1
done
echo "Database is ready!"

# Apply Alembic migrations
echo "Running database migrations..."
uv run alembic upgrade head

echo "Migrations complete. Starting application..."

# Run your application
exec "$@"
