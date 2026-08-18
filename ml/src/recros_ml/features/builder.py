from __future__ import annotations

import json
import logging
import random
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

AUDIO_KEYS = [
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
]


def _genre_set(genres_str: str) -> set[str]:
    if not genres_str or pd.isna(genres_str):
        return set()
    return {g.strip().lower() for g in str(genres_str).split("|") if g.strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _loc_item(items_idx: pd.DataFrame, ik: str) -> pd.Series:
    """Single row for ``ik``; duplicate indices collapse to the first row."""
    row = items_idx.loc[ik]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return row


def build_user_movie_genre_weights(
    interactions: pd.DataFrame,
    items_idx: pd.DataFrame,
    pos_threshold: float,
) -> dict[int, dict[str, float]]:
    weights: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    movie_ix = interactions["domain"] == "movie"
    pos = interactions[movie_ix & (interactions["rating"] >= pos_threshold)]
    for row in pos.itertuples(index=False):
        uid = int(row.user_id)
        ik = str(row.item_key)
        if ik not in items_idx.index:
            continue
        it = _loc_item(items_idx, ik)
        w = float(row.rating) - pos_threshold + 0.1
        for g in _genre_set(str(it["genres_str"])):
            weights[uid][g] += w
    out: dict[int, dict[str, float]] = {}
    for uid, gw in weights.items():
        s = sum(gw.values()) or 1.0
        out[uid] = {k: v / s for k, v in gw.items()}
    return out


def _top_genre_set(profile: dict[str, float], top_k: int = 24) -> set[str]:
    sorted_g = sorted(profile.items(), key=lambda x: -x[1])[:top_k]
    return {g for g, _ in sorted_g}


def row_features(
    item: pd.Series,
    genre_profile: dict[str, float],
    global_year_median: float,
    global_vote_median: float,
) -> dict[str, float]:
    if isinstance(item, pd.DataFrame):
        item = item.iloc[0]

    def _cell(key: str):
        v = item[key]
        if isinstance(v, pd.Series):
            v = v.iloc[0]
        return v

    gprof_top = _top_genre_set(genre_profile)
    gs = _cell("genres_str")
    ig = _genre_set(str(gs))
    genre_j = _jaccard(gprof_top, ig)

    pop_v = _cell("popularity")
    pop = float(pop_v) if pd.notna(pop_v) else 0.0
    year_v = _cell("year")
    year = float(year_v) if pd.notna(year_v) else global_year_median
    avg_v = _cell("avg_rating")
    avg_r = float(avg_v) if pd.notna(avg_v) else global_vote_median

    dom = str(_cell("domain"))

    extra = {}
    try:
        ex = item.get("extra_json", "{}")
        if isinstance(ex, pd.Series):
            ex = ex.iloc[0]
        extra = json.loads(str(ex or "{}"))
    except json.JSONDecodeError:
        extra = {}

    feats: dict[str, float] = {
        "pop_log": float(np.log1p(max(pop, 0.0))),
        "year": year,
        "rating_item": avg_r,
        "genre_jaccard": genre_j,
        "desc_len_log": float(np.log1p(len(str(_cell("description"))))),
        "title_len_log": float(np.log1p(len(str(_cell("title"))))),
        "domain_movie": 1.0 if dom == "movie" else 0.0,
        "domain_music": 1.0 if dom == "music" else 0.0,
        "domain_book": 1.0 if dom == "book" else 0.0,
    }

    for k in AUDIO_KEYS:
        feats[f"audio_{k}"] = float(extra.get(k, 0.0))

    return feats


def build_training_frame(cfg: dict[str, Any]) -> tuple[pd.DataFrame, list[str]]:
    rng = random.Random(int(cfg["split"]["random_seed"]))
    np_rng = np.random.default_rng(int(cfg["split"]["random_seed"]))
    log_cfg = cfg.get("logging") or {}
    progress_every = int(log_cfg.get("feature_progress_every_users", 250))

    processed = cfg["paths"]["processed_dir"]
    log.info("Loading items.parquet from %s", processed)
    items = pd.read_parquet(f"{processed}/items.parquet")
    items = items.drop_duplicates(subset=["item_key"], keep="first").reset_index(drop=True)
    log.info("Loading interactions.parquet...")
    interactions = pd.read_parquet(f"{processed}/interactions.parquet")
    log.info("items=%s interactions=%s", len(items), len(interactions))

    items_idx = items.set_index("item_key", drop=False)

    movie_keys = items.loc[items["domain"] == "movie", "item_key"].astype(str).tolist()
    music_keys = items.loc[items["domain"] == "music", "item_key"].astype(str).tolist()
    book_keys = items.loc[items["domain"] == "book", "item_key"].astype(str).tolist()

    train_cfg = cfg["training"]
    pos_thr = float(train_cfg["positive_rating_threshold"])
    neg_mult = int(train_cfg["negatives_per_positive_movie"])
    cd_n = int(train_cfg["cross_domain_samples_per_user"])
    weak_thr = float(train_cfg["bootstrap_weak_positive_threshold"])
    max_users = train_cfg.get("max_users")
    max_mu = int(train_cfg.get("max_movie_rows_per_user") or 100)
    max_rows = int(train_cfg.get("max_training_rows") or 1_000_000)

    movie_ix = interactions["domain"] == "movie"
    user_counts = interactions.loc[movie_ix].groupby("user_id").size()
    eligible_users = user_counts[user_counts >= 3].index.tolist()
    rng.shuffle(eligible_users)
    if max_users is not None:
        eligible_users = eligible_users[: int(max_users)]

    eligible_set = set(eligible_users)
    log.info("Building genre profiles from positive movie ratings...")
    genre_profiles = build_user_movie_genre_weights(interactions, items_idx, pos_thr)
    log.info("Users with genre profiles=%s", len(genre_profiles))

    year_med = float(np.nanmedian(items["year"].dropna())) if items["year"].notna().any() else 2000.0
    mv = items.loc[items["domain"] == "movie", "avg_rating"]
    global_vote_median = float(np.nanmedian(mv.dropna())) if mv.notna().any() else 3.5

    music_pop_p75 = (
        float(np.percentile(items.loc[items["domain"] == "music", "popularity"].dropna(), 75))
        if music_keys
        else 0.0
    )

    user_ratings: dict[int, dict[str, float]] = defaultdict(dict)
    for row in interactions.loc[movie_ix].itertuples(index=False):
        uid = int(row.user_id)
        if uid not in eligible_set:
            continue
        user_ratings[uid][str(row.item_key)] = float(row.rating)

    rows: list[dict[str, Any]] = []
    movie_key_set = set(movie_keys)
    log.info(
        "Generating pair rows (eligible_users=%s max_training_rows=%s progress_every=%s)...",
        len(eligible_users),
        max_rows,
        progress_every,
    )

    def append_row(uid: int, ik: str, label: int) -> None:
        if ik not in items_idx.index:
            return
        it = _loc_item(items_idx, ik)
        prof = genre_profiles.get(uid, {})
        f = row_features(it, prof, year_med, global_vote_median)
        f["user_id"] = uid
        f["item_key"] = ik
        f["label"] = int(label)
        rows.append(f)

    for ui, uid in enumerate(eligible_users):
        rated = user_ratings.get(uid, {})
        if len(rated) > max_mu:
            subs = rng.sample(sorted(rated.items()), max_mu)
            rated = dict(subs)

        positives = [ik for ik, r in rated.items() if r >= pos_thr]
        negatives_pool = [ik for ik, r in rated.items() if r < pos_thr]
        unseen_movies = list(movie_key_set - set(rated.keys()))

        for ik in positives:
            append_row(uid, ik, 1)
            cand_neg: list[str] = []
            if negatives_pool:
                cand_neg.extend(rng.sample(negatives_pool, min(neg_mult, len(negatives_pool))))
            need = neg_mult - len(cand_neg)
            if need > 0 and unseen_movies:
                take = min(need, len(unseen_movies))
                cand_neg.extend(list(np_rng.choice(unseen_movies, size=take, replace=False)))
            for nk in cand_neg[:neg_mult]:
                append_row(uid, nk, 0)

        prof_set = _top_genre_set(genre_profiles.get(uid, {}))
        for _ in range(cd_n):
            if rng.random() < 0.5 and book_keys:
                bik = rng.choice(book_keys)
                book = _loc_item(items_idx, bik)
                gj = _jaccard(prof_set, _genre_set(str(book["genres_str"])))
                lbl = 1 if gj >= weak_thr else 0
                append_row(uid, bik, lbl)
            elif music_keys:
                mik = rng.choice(music_keys)
                music = _loc_item(items_idx, mik)
                pop_v = music["popularity"]
                if isinstance(pop_v, pd.Series):
                    pop_v = pop_v.iloc[0]
                pop = float(pop_v) if pd.notna(pop_v) else 0.0
                lbl = 1 if pop >= music_pop_p75 else 0
                append_row(uid, mik, lbl)

        if progress_every > 0 and (ui + 1) % progress_every == 0:
            log.info(
                "features progress users=%s/%s accumulated_rows=%s",
                ui + 1,
                len(eligible_users),
                len(rows),
            )

        if len(rows) >= max_rows:
            break

    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    frame = pd.DataFrame(rows)
    feature_cols = sorted([c for c in frame.columns if c not in ("user_id", "item_key", "label")])
    log.info("Built training frame rows=%s cols=%s positive_rate=%.4f", len(frame), len(feature_cols), float(frame["label"].mean()) if len(frame) else 0.0)
    return frame, feature_cols
