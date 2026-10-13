# Recros

Recros is a cross-domain recommendation app for discovering movies, books, and music through one evolving taste profile.

## Get the datasets

The CSVs aren't in git (about 740 MB, Kaggle licenses). Download them once from Kaggle:

```bash
pip install kaggle   # then put your API token in ~/.kaggle/kaggle.json (kaggle.com → Settings → API)
./scripts/fetch_datasets.sh
```

This fills `movie_dataset/`, `music_dataset/` and `book_dataset/`. Sources: [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset), [MovieLens 20M](https://www.kaggle.com/datasets/grouplens/movielens-20m-dataset), [Spotify 1921-2020](https://www.kaggle.com/datasets/vatsalmavani/spotify-dataset), [7k Books](https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata).

## Run the MVP

```bash
python3 -m venv .venv-api
.venv-api/bin/pip install -r apps/api/requirements.txt
PYTHONPATH=apps/api .venv-api/bin/python -m recros_api.seed --reset --limit 800
PYTHONPATH=apps/api .venv-api/bin/uvicorn recros_api.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The app stores local state in `apps/api/data/recros.db` (ignored by git). The seeder reads the downloaded CSV datasets. Users can choose domains, genres, moods, and exploration level; recommendations are scored across domains and updated from like/save/skip feedback.

## Auth and operations

The browser uses a bearer token issued by the guest-user endpoint. API clients can use real credentials:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"you@example.com","password":"at-least-8-chars"}'
```

For a full retrain from all ratings:

```bash
RECROS_ML_CONFIG=ml/config.full.yaml ./scripts/retrain.sh
```

The API hot-loads a changed `ml/artifacts/bundle_latest` on the next model-backed request. A cron example is in `scripts/retrain.cron.example`.

## Container

After running the ML pipeline so `ml/artifacts` exists:

```bash
docker compose up --build
```

The container persists its SQLite database in the `recros_data` volume and serves the app at http://127.0.0.1:8000.

## Project areas

- `apps/api`: FastAPI API, SQLite schema, content-first recommender, and dataset seeder.
- `apps/web`: browser UI for onboarding and recommendations.
- `ml`: existing offline LightGBM training pipeline, kept for the next ranking iteration.
- `run_recros.sh`: one-command local runner after installing `.venv-api`.
