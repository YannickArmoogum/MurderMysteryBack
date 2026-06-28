#!/usr/bin/env sh
set -e

# Wait for the database to accept connections (Postgres). Skipped for sqlite.
case "${DATABASE_URL:-}" in
  postgres*|postgresql*)
    echo "Waiting for database to be ready..."
    python - <<'PY'
import os, time, sys
import sqlalchemy as sa

url = os.environ["DATABASE_URL"]
engine = sa.create_engine(url, pool_pre_ping=True)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        print("Database is ready.")
        sys.exit(0)
    except Exception as exc:
        print(f"  db not ready ({attempt + 1}/30): {exc}")
        time.sleep(2)
print("Database did not become ready in time.", file=sys.stderr)
sys.exit(1)
PY
    ;;
esac

# Apply database migrations
echo "Running alembic migrations..."
alembic upgrade head

# Hand off to the container CMD (uvicorn)
exec "$@"
