# Dataset recovery — October 13, 2026

The project covers **songs, movies and books**. Internal code calls the songs domain
`music`. All six directed transfers are supported by the evidence lab: each of the
three domains can be the source and either of the other two can be the target.

The first local inspection found no raw datasets or original trained artifacts.
We then checked ignored files, symlinks, every local Git commit, dangling Git trees,
and likely dataset/archive names under Downloads and chronicles. The local checkout
was at `5bd8fa6`, but a live remote check found two newer commits. Fetching them
revealed `scripts/fetch_datasets.sh` at `6fcda21`, merged into main as `00a02c4`.
The new upstream README explicitly says the CSVs are not committed to Git.

We restored the public sources identified by that script through Kaggle's official
`kagglehub` client. No Kaggle login was needed in this run. The source files were
downloaded afresh; they were not hiding in the earlier checkout. The original
trained LightGBM bundle, generated training pairs and historical metric files were
not recovered.

| File | Raw CSV rows | What it provides |
|---|---:|---|
| `movie_dataset/movies_metadata.csv` | 45,466 | Movie titles, descriptions and metadata; not all raw rows survive cleaning |
| `movie_dataset/keywords.csv` | 46,419 | Movie keywords |
| `movie_dataset/links.csv` | 45,843 | MovieLens/TMDB ID mapping |
| `movie_dataset/rating.csv` | 20,000,263 | Actual movie user ratings and timestamps |
| `music_dataset/data_music.csv` | 170,653 | Song/artist metadata and audio features |
| `book_dataset/book_data.csv` | 6,810 | Book descriptions, categories and aggregate ratings |

Exact file sizes, headers, sources and SHA-256 hashes are in [DATA_AUDIT.json](DATA_AUDIT.json).
These are raw record counts, not counts of unique valid items. Raw datasets remain
Git-ignored. Their source terms continue to apply.

The movie user IDs do not identify the same people in the song or book datasets.
In fact, these two files have no individual user-interaction table to join. The
original code constructs weak book/music targets; those are training conveniences,
not independently observed cross-domain preferences. Catalog coverage across three
domains and measured preference transfer are different claims.

A new ingestion run with `ml/config.mac_air.yaml` produced **222,896 unique items**
(45,433 movies, 170,653 songs, 6,810 books), 6,034 users and 899,176 movie
interactions from the first 900,000 rating rows. This confirms pipeline execution;
it is not a representative sample or a new training result. There are 675 joined
interactions whose movie has no cleaned catalog record; filter or explicitly handle
these before a future training/evaluation run. See [INGEST_CHECK.json](INGEST_CHECK.json).
The resulting parquet files are local and ignored by Git.

The demo SQLite database now contains **2,400 real items: 800 per domain**. Its
original heuristic recommendations can be explored at `http://127.0.0.1:8008/`.
The evidence lab at `/lab` uses 12 selected, sourced works and cached DeepSeek
annotations. These are separate demonstrations; the 2,400-item catalog is not all
LLM-annotated. The original seeder chooses popular items, so this catalog is not a
representative long-tail evaluation set.

Restore or check the files again:

```bash
.venv-research/bin/python -m pip install kagglehub==1.0.2
.venv-research/bin/python scripts/fetch_public_datasets.py
# No network or download:
.venv-research/bin/python scripts/fetch_public_datasets.py --audit-only
```

Existing nonempty files are retained, schema checked, counted and hashed. Movies
follow the current public Kaggle version; books and songs use the versions retrieved
in this run. Compare hashes before interpreting results as an exact reproduction.

Sources: [upstream dataset script](https://github.com/SachPlayZ/Recros/blob/6fcda21ff19723dbc802f6855d1bcb82136268af/scripts/fetch_datasets.sh),
[Movies](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset),
[ratings](https://www.kaggle.com/datasets/grouplens/movielens-20m-dataset),
[songs](https://www.kaggle.com/datasets/vatsalmavani/spotify-dataset),
[books](https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata).
