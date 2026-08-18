"""Load an exported bundle and score a few synthetic rows (sanity check)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from recros_ml.inference import RankerInference


def _synthetic_rows() -> list[dict]:
    """Minimal valid feature vectors: one movie-like, one music-like, one book-like."""
    base_movie = {
        "pop_log": 3.0,
        "year": 2010.0,
        "rating_item": 7.0,
        "genre_jaccard": 0.4,
        "desc_len_log": 5.0,
        "title_len_log": 3.0,
        "domain_movie": 1.0,
        "domain_music": 0.0,
        "domain_book": 0.0,
        "audio_valence": 0.0,
        "audio_acousticness": 0.0,
        "audio_danceability": 0.0,
        "audio_energy": 0.0,
        "audio_instrumentalness": 0.0,
        "audio_liveness": 0.0,
        "audio_loudness": 0.0,
        "audio_speechiness": 0.0,
        "audio_tempo": 0.0,
        "audio_duration_ms": 0.0,
    }
    music = {
        **{k: 0.0 for k in base_movie if k.startswith("audio_")},
        "pop_log": 4.0,
        "year": 2019.0,
        "rating_item": 3.5,
        "genre_jaccard": 0.1,
        "desc_len_log": 0.0,
        "title_len_log": 4.0,
        "domain_movie": 0.0,
        "domain_music": 1.0,
        "domain_book": 0.0,
        "audio_valence": 0.7,
        "audio_acousticness": 0.2,
        "audio_danceability": 0.8,
        "audio_energy": 0.75,
        "audio_instrumentalness": 0.05,
        "audio_liveness": 0.1,
        "audio_loudness": -5.0,
        "audio_speechiness": 0.05,
        "audio_tempo": 120.0,
        "audio_duration_ms": 200000.0,
    }
    book = {
        **base_movie,
        "domain_movie": 0.0,
        "domain_music": 0.0,
        "domain_book": 1.0,
        "rating_item": 4.2,
        "genre_jaccard": 0.25,
        "desc_len_log": 7.0,
        "audio_valence": 0.0,
        "audio_acousticness": 0.0,
        "audio_danceability": 0.0,
        "audio_energy": 0.0,
        "audio_instrumentalness": 0.0,
        "audio_liveness": 0.0,
        "audio_loudness": 0.0,
        "audio_speechiness": 0.0,
        "audio_tempo": 0.0,
        "audio_duration_ms": 0.0,
    }
    return [
        {"label": "synthetic_movie", **base_movie},
        {"label": "synthetic_music", **music},
        {"label": "synthetic_book", **book},
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score synthetic rows with a trained bundle.")
    parser.add_argument(
        "--bundle",
        type=str,
        default=os.environ.get("RECROS_MODEL_BUNDLE", "ml/artifacts/bundle_latest"),
        help="Path to bundle dir (contains ranker_lgb.txt, feature_columns.json, train_meta.json)",
    )
    args = parser.parse_args()

    bundle = Path(args.bundle).resolve()
    if not bundle.is_dir():
        raise SystemExit(f"Bundle directory not found: {bundle}")

    rk = RankerInference.from_bundle(bundle)
    rows = _synthetic_rows()
    labels = [r.pop("label") for r in rows]

    scores = rk.predict_dict_rows(rows)
    print(f"bundle={bundle}")
    print(f"best_iteration={rk.best_iteration}  n_features={len(rk.feature_columns)}")
    for lab, sc in sorted(zip(labels, scores.tolist(), strict=True), key=lambda x: -x[1]):
        print(f"  score={sc:.6f}  {lab}")


if __name__ == "__main__":
    main()
