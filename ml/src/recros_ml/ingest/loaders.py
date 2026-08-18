from __future__ import annotations

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

log = logging.getLogger(__name__)


def _parse_genre_like(cell: Any) -> list[str]:
    if pd.isna(cell) or cell == "":
        return []
    if isinstance(cell, list):
        return [str(x) for x in cell]
    s = str(cell)
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, list):
            names = []
            for x in parsed:
                if isinstance(x, dict) and "name" in x:
                    names.append(str(x["name"]))
                elif isinstance(x, str):
                    names.append(x)
            return names
    except (SyntaxError, ValueError, TypeError):
        pass
    return [g.strip() for g in re.split(r"[|,;/]", s) if g.strip()]


def _parse_artists(cell: Any) -> str:
    if pd.isna(cell):
        return ""
    if isinstance(cell, str):
        try:
            parsed = ast.literal_eval(cell)
            if isinstance(parsed, list):
                return "; ".join(str(x) for x in parsed)
        except (SyntaxError, ValueError):
            pass
        return cell
    return str(cell)


def load_movies_metadata(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False, on_bad_lines="skip")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"]).drop_duplicates(subset=["id"])
    df["id"] = df["id"].astype(int)
    return df


def load_keywords(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)
    return df


def load_links(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["movieId"] = pd.to_numeric(df["movieId"], errors="coerce").astype("Int64")
    df["tmdbId"] = pd.to_numeric(df["tmdbId"], errors="coerce").astype("Int64")
    return df.dropna(subset=["movieId", "tmdbId"])


def load_ratings(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    read_kwargs = {"usecols": ["userId", "movieId", "rating", "timestamp"]}
    if max_rows is not None:
        log.info("Reading at most %s ratings rows from %s", max_rows, path)
        read_kwargs["nrows"] = int(max_rows)
    df = pd.read_csv(path, **read_kwargs)
    df["userId"] = pd.to_numeric(df["userId"], errors="coerce").astype("Int64")
    df["movieId"] = pd.to_numeric(df["movieId"], errors="coerce").astype("Int64")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    numeric_timestamp = pd.to_numeric(df["timestamp"], errors="coerce")
    if numeric_timestamp.notna().mean() >= 0.9:
        timestamp = numeric_timestamp
    else:
        parsed_timestamp = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        timestamp = parsed_timestamp.map(
            lambda value: int(value.timestamp()) if pd.notna(value) else pd.NA
        )
    df["timestamp"] = timestamp.astype("Int64")
    return df.dropna(subset=["userId", "movieId", "rating", "timestamp"])


def load_music(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def load_books(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def attach_keywords(movies: pd.DataFrame, keywords: pd.DataFrame) -> pd.DataFrame:
    kw = keywords.rename(columns={"keywords": "keywords_raw"})
    merged = movies.merge(kw, on="id", how="left")
    tags: list[str] = []
    for cell in merged["keywords_raw"].fillna(""):
        tags.append("|".join(_parse_genre_like(cell)))
    merged["tags_str"] = tags
    merged = merged.drop(columns=["keywords_raw"], errors="ignore")
    return merged


def build_movie_items(movies: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in movies.iterrows():
        sid = int(r["id"])
        genres = _parse_genre_like(r.get("genres"))
        title = str(r.get("title") or "")[:2000]
        overview = str(r.get("overview") or "")[:8000]
        year = pd.to_datetime(r.get("release_date"), errors="coerce")
        year_val = float(year.year) if pd.notna(year) else float("nan")
        pop = float(r["popularity"]) if pd.notna(r.get("popularity")) else 0.0
        vote_avg = float(r["vote_average"]) if pd.notna(r.get("vote_average")) else float("nan")
        rows.append(
            {
                "domain": "movie",
                "source_id": str(sid),
                "item_key": f"movie:{sid}",
                "title": title,
                "description": overview,
                "creators": "",
                "genres_str": "|".join(genres),
                "tags_str": str(r.get("tags_str") or ""),
                "year": year_val,
                "popularity": pop,
                "avg_rating": vote_avg,
                "extra_json": json.dumps({}),
            }
        )
    return pd.DataFrame(rows)


def build_music_items(music: pd.DataFrame) -> pd.DataFrame:
    audio_cols = [
        "valence",
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "tempo",
        "duration_ms",
        "explicit",
        "mode",
        "key",
    ]
    rows = []
    for _, r in music.iterrows():
        sid = str(r["id"])
        artists = _parse_artists(r.get("artists"))
        year_val = float(r["year"]) if pd.notna(r.get("year")) else float("nan")
        pop = float(r["popularity"]) if pd.notna(r.get("popularity")) else 0.0
        extra = {c: float(r[c]) if pd.notna(r.get(c)) else 0.0 for c in audio_cols if c in music.columns}
        rows.append(
            {
                "domain": "music",
                "source_id": sid,
                "item_key": f"music:{sid}",
                "title": str(r.get("name") or "")[:2000],
                "description": "",
                "creators": artists[:4000],
                "genres_str": "",
                "tags_str": "",
                "year": year_val,
                "popularity": pop,
                "avg_rating": float("nan"),
                "extra_json": json.dumps(extra),
            }
        )
    return pd.DataFrame(rows)


def build_book_items(books: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in books.iterrows():
        sid = str(r.get("isbn13") or r.get("isbn10") or "").strip()
        if not sid:
            continue
        cats = _parse_genre_like(r.get("categories"))
        authors = str(r.get("authors") or "")[:4000]
        desc = str(r.get("description") or "")[:8000]
        title = str(r.get("title") or "")[:2000]
        subtitle = str(r.get("subtitle") or "")
        full_title = f"{title} {subtitle}".strip()
        year_val = float(r["published_year"]) if pd.notna(r.get("published_year")) else float("nan")
        avg_r = float(r["average_rating"]) if pd.notna(r.get("average_rating")) else float("nan")
        rc = float(r["ratings_count"]) if pd.notna(r.get("ratings_count")) else 0.0
        extra = {"ratings_count": rc, "num_pages": float(r["num_pages"]) if pd.notna(r.get("num_pages")) else 0.0}
        rows.append(
            {
                "domain": "book",
                "source_id": sid,
                "item_key": f"book:{sid}",
                "title": full_title,
                "description": desc,
                "creators": authors,
                "genres_str": "|".join(cats),
                "tags_str": "",
                "year": year_val,
                "popularity": rc,
                "avg_rating": avg_r,
                "extra_json": json.dumps(extra),
            }
        )
    return pd.DataFrame(rows)


def build_interactions(
    ratings: pd.DataFrame,
    links: pd.DataFrame,
) -> pd.DataFrame:
    m = ratings.merge(links, on="movieId", how="inner")
    m = m.dropna(subset=["tmdbId"])
    m["tmdbId"] = m["tmdbId"].astype(int)
    out = pd.DataFrame(
        {
            "user_id": m["userId"].astype(int),
            "item_key": "movie:" + m["tmdbId"].astype(str),
            "domain": "movie",
            "rating": m["rating"].astype(float),
            "timestamp": m["timestamp"].astype("int64"),
        }
    )
    return out


def build_users(interactions: pd.DataFrame) -> pd.DataFrame:
    u = interactions["user_id"].unique()
    return pd.DataFrame({"user_id": u}).sort_values("user_id").reset_index(drop=True)


def build_all_tables(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ds = cfg["datasets"]
    ingest_cfg = cfg.get("ingest") or {}
    seed = int(cfg.get("split", {}).get("random_seed", 42))

    log.info("Loading movies_metadata: %s", ds["movies_metadata"])
    movies_raw = load_movies_metadata(Path(ds["movies_metadata"]))
    log.info("movies_metadata rows=%s", len(movies_raw))
    log.info("Loading keywords: %s", ds["movies_keywords"])
    keywords = load_keywords(Path(ds["movies_keywords"]))
    log.info("Loading links: %s", ds["movies_links"])
    links = load_links(Path(ds["movies_links"]))
    log.info("Loading ratings: %s", ds["movies_ratings"])
    mr = ingest_cfg.get("max_ratings_rows")
    ratings = load_ratings(Path(ds["movies_ratings"]), max_rows=int(mr) if mr is not None else None)
    log.info("ratings rows=%s", len(ratings))
    log.info("Loading music: %s", ds["music_tracks"])
    music_raw = load_music(Path(ds["music_tracks"]))
    log.info("music rows=%s", len(music_raw))
    log.info("Loading books: %s", ds["books"])
    books_raw = load_books(Path(ds["books"]))
    log.info("books rows=%s", len(books_raw))

    log.info("Building normalized movie/music/book item rows...")
    movies_kw = attach_keywords(movies_raw, keywords)
    items_movie = build_movie_items(movies_kw)
    items_music = build_music_items(music_raw)
    items_book = build_book_items(books_raw)
    items = pd.concat([items_movie, items_music, items_book], ignore_index=True)
    items = items.drop_duplicates(subset=["item_key"], keep="first").reset_index(drop=True)
    log.info(
        "Catalog items=%s (movie=%s music=%s book=%s)",
        len(items),
        len(items_movie),
        len(items_music),
        len(items_book),
    )

    log.info("Building interactions from ratings x links...")
    interactions = build_interactions(ratings, links)
    log.info("interactions rows=%s", len(interactions))
    users = build_users(interactions)
    log.info("distinct users=%s", len(users))
    return items, users, interactions
