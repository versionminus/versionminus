#!/bin/sh
set -e
# Locate original postgres entrypoint (official image path)
ORIG_ENTRYPOINT="/usr/local/bin/docker-entrypoint.sh"
if [ ! -x "$ORIG_ENTRYPOINT" ]; then
  echo "[wrapper] Original entrypoint not found at $ORIG_ENTRYPOINT" >&2
  exit 1
fi

# Start postgres in background using original entrypoint
"$ORIG_ENTRYPOINT" postgres &
PG_PID=$!
# Wait for postgres to accept connections
echo "[wrapper] Waiting for Postgres to become available..."
RETRIES=60
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h 127.0.0.1 -p 5432 >/dev/null 2>&1; do
  RETRIES=$((RETRIES-1))
  if [ $RETRIES -le 0 ]; then
    echo "[wrapper] Postgres did not become ready in time" >&2
    exit 1
  fi
  sleep 1
done
echo "[wrapper] Postgres is ready, applying migrations..."
PYTHONPATH=/app alembic upgrade head || { echo "[wrapper] Migration failed" >&2; kill $PG_PID; exit 1; }
echo "[wrapper] Migrations complete. Attaching to Postgres foreground..."
wait $PG_PID
