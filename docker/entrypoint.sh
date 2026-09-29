#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

until pg_isready \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER"
do
    sleep 1
done

echo "PostgreSQL is ready."

echo "Applying migrations..."

alembic upgrade head

echo "Starting FastAPI..."

#exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}"

#ABS_Inventory