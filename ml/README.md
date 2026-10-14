# Recros ML pipeline (local / Apple Silicon)

Runs entirely on CPU. Tested layout: **Python 3.11+**, repo root = directory that contains `ml/` and the `*_dataset/` folders from the Kaggle downloads (`./scripts/fetch_datasets.sh`) (paths in `ml/config.yaml`).

## One-shot run (Mac M4 Air friendly)

From the **repository root**:

```bash
chmod +x ml/run_local.sh
./ml/run_local.sh
```

Optional:

- Use the lighter preset (less RAM, faster): `RECROS_ML_CONFIG=ml/config.mac_air.yaml ./ml/run_local.sh`
- Use all rows from `movie_dataset/rating.csv` while keeping training pairs bounded: `RECROS_ML_CONFIG=ml/config.full.yaml ./ml/run_local.sh`
- Override thread caps (avoid oversubscription on laptops): `OMP_NUM_THREADS=8 ./ml/run_local.sh`

### Logs (always streaming)

- Shell script prints **timestamped phase banners** (`=== recros_ml.train ===`).
- Python logs go to **stderr** with timestamps and flush after every line (`PYTHONUNBUFFERED=1` is set in `run_local.sh`).
- Tune verbosity: `RECROS_LOG_LEVEL=DEBUG ./ml/run_local.sh` or per-step `python -m recros_ml.train -v`.
- Feature generation prints progress every **N users** (`logging.feature_progress_every_users` in YAML).
- LightGBM validation metrics print every **N rounds** (`logging.lightgbm_eval_period` in YAML).
- Save full transcript: `./ml/run_local.sh 2>&1 | tee ml/last_run.log`

When switching between `config.yaml` and `config.mac_air.yaml`, let **`ingest` run again** (the script always does) so `interactions.parquet` matches the preset’s `max_ratings_rows`. If you previously ingested with a larger sample, delete `ml/data/processed/` before rerunning with the lighter preset.

## Manual steps

```bash
cd /path/to/Recros
python3 -m venv .venv
source .venv/bin/activate
pip install -e ml/

python -m recros_ml.ingest --config ml/config.yaml
python -m recros_ml.build_features --config ml/config.yaml
python -m recros_ml.train --config ml/config.yaml
python -m recros_ml.evaluate --config ml/config.yaml
python -m recros_ml.export --config ml/config.yaml
```

Inference loads the latest bundle under `ml/artifacts/bundle_latest/` (symlink when supported; otherwise a full directory copy).

## Apple Silicon / LightGBM

Install wheels with `pip install -e ml/` (no conda required). If training crashes on import with **OpenMP / `libomp` missing**:

```bash
brew install libomp
```

Then retry training. If it still fails, see [LightGBM macOS install notes](https://github.com/microsoft/LightGBM/tree/master/python-package).

## RAM notes

- Default `ml/config.yaml` is tuned for ~**8–16 GB** unified memory (samples ratings and caps training rows).
- If the machine swaps heavily, switch to `ml/config.mac_air.yaml` or lower `ingest.max_ratings_rows` and `training.max_training_rows` in `ml/config.yaml`.

## October 14 research tools

The book/song extension uses separately downloaded public interaction sources.
It preserves the earlier movie run. See the
[three-domain report](../docs/milestone2/hierarchy/domains/RESULT.md) for frozen
protocols, split limitations and full-catalog baseline comparisons.

```bash
.venv-research/bin/python scripts/fetch_domain_holdout.py
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.domain_holdout prepare book
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.domain_holdout validate book
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.domain_holdout test book
# Repeat with music. Completed protocols and runs refuse overwrite.
```

Run from the repository root with the existing research environment:

```bash
# Exact constructed mechanism probe (no inference)
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.decision_probe

# Replay the frozen 24-task comparison, including cached DeepSeek responses
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.policy_benchmark

# Build familiar-work search from already recovered local data
.venv-research/bin/python scripts/build_familiar_catalog.py

# Summarize local personal-trial records; output stays beside the ignored DB
RECROS_DB=apps/api/data/milestone2-demo.db PYTHONPATH=ml/src:apps/api \
  .venv-research/bin/python -m recros_ml.research.personal_trial_report
```

See [decision lab](../docs/milestone2/DECISION_LAB.md) and
[representation audit](../docs/milestone2/REPRESENTATION_AUDIT.md).
The controlled policy result is a three-way tie among exact planning, information
gain and DeepSeek. It does not establish an SLM advantage or human preference gain.
Do not mix the scripted cases with the movie-rating benchmark or count local demo
records as participant responses.
