#!/bin/sh
set -e

MODE="${RUN_MODE:-api}"

if [ "$MODE" = "worker" ]; then
  echo "[entrypoint] $(date -Iseconds) starting celery worker (beat enabled)"
  exec celery -A src.config.celery_app worker -B -l info --concurrency=2
fi

echo "[entrypoint] $(date -Iseconds) alembic upgrade head"
alembic upgrade head || {
  echo "[entrypoint] alembic failed, falling back to metadata init"
  python -c "from src.config.database import init_db; init_db()"
}

if [ "${SEED_DEMO:-false}" = "true" ]; then
  echo "[entrypoint] $(date -Iseconds) seeding demo data"
  python scripts/seed_demo.py || echo "[entrypoint] seed failed (non-blocking)"
fi

echo "[entrypoint] $(date -Iseconds) starting uvicorn on :8000"
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log
