#!/usr/bin/env bash
# Run the full ML pipeline from the repo root (works on Apple Silicon).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-8}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-8}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-8}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-8}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-8}"

PYTHON="${PYTHON:-python3}"
CFG="${RECROS_ML_CONFIG:-ml/config.yaml}"

if [[ ! -d .venv ]]; then
  echo "Creating .venv with ${PYTHON}..."
  "${PYTHON}" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip setuptools wheel -q
pip install -e ml/

echo "Using config: ${CFG}"
python -m recros_ml.ingest --config "${CFG}"
python -m recros_ml.build_features --config "${CFG}"
python -m recros_ml.train --config "${CFG}"
python -m recros_ml.evaluate --config "${CFG}"
python -m recros_ml.export --config "${CFG}"

echo "Done. Latest bundle: ml/artifacts/bundle_latest/"
