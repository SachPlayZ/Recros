from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

try:
    import lightgbm as lgb
    import numpy as np
except (ImportError, OSError):  # Optional native libraries (e.g. libomp) may also be absent.
    lgb = None
    np = None


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BUNDLE = ROOT / "ml" / "artifacts" / "bundle_latest"
AUDIO_KEYS = [
    "acousticness", "danceability", "duration_ms", "energy", "instrumentalness",
    "liveness", "loudness", "speechiness", "tempo", "valence",
]


def _genre_set(value: str) -> set[str]:
    return {x.strip().lower() for x in (value or "").split("|") if x.strip()}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


class OnlineRanker:
    def __init__(self, bundle_dir: Path):
        if lgb is None or np is None:
            raise RuntimeError("lightgbm and numpy are required for online ranking")
        self.bundle_dir = bundle_dir.resolve()
        self.model = lgb.Booster(model_file=str(self.bundle_dir / "ranker_lgb.txt"))
        self.feature_columns = json.loads((self.bundle_dir / "feature_columns.json").read_text())
        meta = json.loads((self.bundle_dir / "train_meta.json").read_text())
        self.best_iteration = int(meta.get("best_iteration") or -1)
        defaults = meta.get("feature_defaults") or {}
        self.year_default = float(defaults.get("year", 2000.0))
        self.rating_default = float(defaults.get("rating_item", 3.5))

    def feature_row(self, item: Any, genre_profile: dict[str, float]) -> dict[str, float]:
        item_genres = _genre_set(item["genres"])
        top_genres = {genre for genre, _ in sorted(genre_profile.items(), key=lambda pair: -pair[1])[:24]}
        metadata = json.loads(item["metadata"] or "{}")
        domain = str(item["domain"])
        row: dict[str, float] = {
            "pop_log": math.log1p(max(float(item["popularity"] or 0.0), 0.0)),
            "year": float(item["year"] or self.year_default),
            "rating_item": float(item["rating"] or self.rating_default),
            "genre_jaccard": _jaccard(top_genres, item_genres),
            "desc_len_log": math.log1p(len(str(item["description"] or ""))),
            "title_len_log": math.log1p(len(str(item["title"] or ""))),
            "domain_movie": 1.0 if domain == "movie" else 0.0,
            "domain_music": 1.0 if domain == "music" else 0.0,
            "domain_book": 1.0 if domain == "book" else 0.0,
        }
        for key in AUDIO_KEYS:
            value = metadata.get(key, 0.0)
            try:
                row[f"audio_{key}"] = float(value or 0.0)
            except (TypeError, ValueError):
                row[f"audio_{key}"] = 0.0
        return row

    def score(self, items: list[Any], genre_profile: dict[str, float]) -> list[float]:
        rows = [self.feature_row(item, genre_profile) for item in items]
        matrix = np.asarray([[row[column] for column in self.feature_columns] for row in rows], dtype=np.float32)
        return [float(value) for value in self.model.predict(matrix, num_iteration=self.best_iteration)]


_RANKER: OnlineRanker | None = None
_RANKER_ERROR: str | None = None
_RANKER_MTIME: int | None = None


def get_ranker() -> OnlineRanker | None:
    global _RANKER, _RANKER_ERROR, _RANKER_MTIME
    bundle = Path(os.getenv("RECROS_RANKER_BUNDLE", str(DEFAULT_BUNDLE)))
    model_path = bundle / "ranker_lgb.txt"
    if not model_path.exists():
        _RANKER_ERROR = f"bundle not found: {bundle}"
        return None
    mtime = model_path.stat().st_mtime_ns
    if _RANKER is not None and _RANKER_MTIME == mtime:
        return _RANKER
    try:
        _RANKER = OnlineRanker(bundle)
        _RANKER_MTIME = mtime
    except Exception as exc:  # pragma: no cover - exercised by missing/broken deployments.
        _RANKER_ERROR = str(exc)
        return None
    return _RANKER


def ranker_status() -> dict[str, Any]:
    ranker = get_ranker()
    if ranker is None:
        return {"enabled": False, "error": _RANKER_ERROR}
    return {
        "enabled": True,
        "bundle": str(ranker.bundle_dir),
        "features": len(ranker.feature_columns),
        "best_iteration": ranker.best_iteration,
    }
