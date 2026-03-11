#!/bin/sh
set -e
# Wait for postgres (handled by depends_on + healthcheck in compose)
# Optional: run migrations if not in init — already in /docker-entrypoint-initdb.d
# Load sample data if DB is empty (optional, can be done manually)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
