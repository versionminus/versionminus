#!/bin/sh
set -e
# Derive Postgres env vars from licodex.core.config (logged for visibility)
echo "[db init] deriving postgres env from licodex.core.config"
python3 - <<'PY'
from licodex.core.config import get_settings
s = get_settings()
print(s.as_postgres_env_exports())
PY
