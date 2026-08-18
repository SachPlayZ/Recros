#!/usr/bin/env bash
set -euo pipefail

if ! python - <<'PY'
from recros_api.db import get_conn, init_db
init_db()
with get_conn() as conn:
    count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
raise SystemExit(0 if count else 1)
PY
then
  python -m recros_api.seed --limit "${RECROS_SEED_LIMIT:-800}"
fi

exec uvicorn recros_api.main:app --host 0.0.0.0 --port "${PORT:-8000}"

