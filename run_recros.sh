#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${RECROS_PYTHON:-$ROOT_DIR/.venv-api/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing $PYTHON_BIN. Run: $ROOT_DIR/.venv-api/bin/pip install -r apps/api/requirements.txt"
  exit 1
fi

cd "$ROOT_DIR"
PYTHONPATH=apps/api "$PYTHON_BIN" -m recros_api.seed --limit "${RECROS_SEED_LIMIT:-800}"
PYTHONPATH=apps/api "$PYTHON_BIN" -m uvicorn recros_api.main:app --host "${RECROS_HOST:-127.0.0.1}" --port "${RECROS_PORT:-8000}"
