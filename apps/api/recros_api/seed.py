from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from pathlib import Path
from typing import Any

from .db import ROOT, get_conn, init_db


def number(value: Any, fallback: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else fallback
    except (TypeError, ValueError):
        return fallback


def listish(value: Any) -> list[str]:
    if not value:
        return []
    try:
        parsed = ast.literal_eval(str(value))
        if isinstance(parsed, list):
            return [str(x.get("name", "")) if isinstance(x, dict) else str(x) for x in parsed if str(x)]
    except (SyntaxError, ValueError):
        pass
    return [x.strip() for x in str(value).replace(",", "|").split("|") if x.strip()]


def movie_rows(path: Path, limit: int) -> list[tuple]:
    rows = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        for raw in csv.DictReader(handle):
            if not raw.get("id") or not raw.get("title") or raw.get("title") == "nan":
                continue
            try:
                movie_id = str(int(float(raw["id"])))
            except ValueError:
                continue
            genres = listish(raw.get("genres"))
            poster = raw.get("poster_path") or ""
            image = f"https://image.tmdb.org/t/p/w500{poster}" if poster.startswith("/") else ""
            rows.append(
                (
                    f"movie:{movie_id}", "movie", raw["title"][:2000], (raw.get("overview") or "")[:8000], "",
                    "|".join(genres), "", number(raw.get("release_date", "")[:4], 0),
                    number(raw.get("popularity")), number(raw.get("vote_average"), 0), image, "{}",
                )
            )
    rows.sort(key=lambda row: row[8], reverse=True)
    return rows[:limit]


def music_rows(path: Path, limit: int) -> list[tuple]:
    rows = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        for raw in csv.DictReader(handle):
            if not raw.get("id") or not raw.get("name"):
                continue
            artists = raw.get("artists") or ""
            try:
                parsed = ast.literal_eval(artists)
                if isinstance(parsed, list):
                    artists = ", ".join(str(x) for x in parsed)
            except (SyntaxError, ValueError):
                pass
            extra = {
                key: number(raw.get(key))
                for key in (
                    "valence", "acousticness", "danceability", "energy", "instrumentalness",
                    "liveness", "loudness", "speechiness", "tempo", "duration_ms",
                )
            }
            rows.append(
                (
                    f"music:{raw['id']}", "music", raw["name"][:2000], "", artists[:4000], "", "",
                    number(raw.get("year")), number(raw.get("popularity")), None, "", json.dumps(extra),
                )
            )
    rows.sort(key=lambda row: row[8], reverse=True)
    return rows[:limit]


def book_rows(path: Path, limit: int) -> list[tuple]:
    rows = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        for raw in csv.DictReader(handle):
            source = (raw.get("isbn13") or raw.get("isbn10") or "").strip()
            title = (raw.get("title") or "").strip()
            if not source or not title:
                continue
            subtitle = (raw.get("subtitle") or "").strip()
            categories = listish(raw.get("categories"))
            creators = (raw.get("authors") or "")[:4000]
            extra = {"ratings_count": number(raw.get("ratings_count")), "pages": number(raw.get("num_pages"))}
            rows.append(
                (
                    f"book:{source}", "book", f"{title} {subtitle}".strip()[:2000], (raw.get("description") or "")[:8000],
                    creators, "|".join(categories), "", number(raw.get("published_year")),
                    number(raw.get("ratings_count")), number(raw.get("average_rating")), raw.get("thumbnail") or "", json.dumps(extra),
                )
            )
    rows.sort(key=lambda row: row[8], reverse=True)
    return rows[:limit]


def seed(limit: int, reset: bool) -> None:
    init_db()
    movie_path = ROOT / "movie_dataset" / "movies_metadata.csv"
    music_path = ROOT / "music_dataset" / "data_music.csv"
    book_path = ROOT / "book_dataset" / "book_data.csv"
    rows = movie_rows(movie_path, limit) + music_rows(music_path, limit) + book_rows(book_path, limit)
    with get_conn() as conn:
        if reset:
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM profiles")
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM items")
        conn.executemany(
            """INSERT OR REPLACE INTO items
               (id, domain, title, description, creators, genres, tags, year, popularity, rating, image_url, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    print(f"Seeded {count} items ({limit} per domain) into {__import__('recros_api.db', fromlist=['DB_PATH']).DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Recros from the bundled CSV datasets")
    parser.add_argument("--limit", type=int, default=800, help="items per domain")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    seed(args.limit, args.reset)
