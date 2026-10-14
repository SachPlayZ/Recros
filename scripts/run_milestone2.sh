#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
PYTHON_BIN="${RECROS_PYTHON:-$ROOT_DIR/.venv-research/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo 'Create .venv-research and install ml/requirements.research.txt first.' >&2
  exit 1
fi
export PYTHONPATH="$ROOT_DIR/apps/api:$ROOT_DIR/ml/src${PYTHONPATH:+:$PYTHONPATH}"
export RECROS_DB="${RECROS_DB:-$ROOT_DIR/apps/api/data/milestone2-demo.db}"
exec "$PYTHON_BIN" -m uvicorn recros_api.main:app --host 127.0.0.1 --port "${RECROS_PORT:-8008}"
