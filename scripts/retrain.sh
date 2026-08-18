#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

CONFIG="${RECROS_ML_CONFIG:-ml/config.full.yaml}"
THREADS="${OMP_NUM_THREADS:-4}"
export RECROS_ML_CONFIG="$CONFIG"
export OMP_NUM_THREADS="$THREADS"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-$THREADS}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-$THREADS}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-$THREADS}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-$THREADS}"

exec ./ml/run_local.sh 2>&1 | tee "ml/retrain_$(date -u +%Y%m%dT%H%M%SZ).log"
