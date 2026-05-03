from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from recros_ml.config import load_config


def _dcg(relevances: np.ndarray, k: int) -> float:
    rel = np.asarray(relevances, dtype=float)[:k]
    if rel.size == 0:
        return 0.0
    gains = (2.0**rel - 1.0) / np.log2(np.arange(2, rel.size + 2))
    return float(gains.sum())


def ndcg_at_k(relevances: np.ndarray, k: int) -> float:
    rel = np.asarray(relevances, dtype=float)
    ideal = np.sort(rel)[::-1]
    idcg = _dcg(ideal, k)
    if idcg <= 0:
        return 0.0
    return _dcg(rel, k) / idcg


def recall_at_k(relevances: np.ndarray, k: int) -> float:
    rel = np.asarray(relevances, dtype=float)
    positives = (rel > 0).sum()
    if positives == 0:
        return 0.0
    return float((rel[:k] > 0).sum()) / positives


def average_precision_at_k(relevances: np.ndarray, k: int) -> float:
    rel = np.asarray(relevances, dtype=float)[:k]
    if rel.sum() == 0:
        return 0.0
    precisions = []
    hits = 0
    for i in range(len(rel)):
        if rel[i] > 0:
            hits += 1
            precisions.append(hits / (i + 1))
    return float(np.mean(precisions)) if precisions else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline ranking metrics on held-out users.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    feat_dir = Path(cfg["paths"]["features_dir"])
    art_dir = Path(cfg["paths"]["artifacts_dir"])

    df = pd.read_parquet(feat_dir / "train_pairs.parquet")
    feature_cols: list[str] = json.loads((feat_dir / "feature_columns.json").read_text())
    val_users = set(json.loads((art_dir / "val_users.json").read_text()))

    train_meta = json.loads((art_dir / "train_meta.json").read_text())
    best_it = int(train_meta.get("best_iteration") or -1)

    model = lgb.Booster(model_file=str(art_dir / "ranker_lgb.txt"))

    val_df = df[df["user_id"].isin(val_users)].copy()
    X = val_df[feature_cols]
    val_df["score"] = model.predict(X, num_iteration=best_it)

    ks = [int(k) for k in cfg["evaluation"]["k_list"]]
    k_max = max(ks)
    cap = int(cfg["evaluation"]["ranking_candidates_per_user"])

    ndcgs: dict[int, list[float]] = defaultdict(list)
    recalls: dict[int, list[float]] = defaultdict(list)
    maps: dict[int, list[float]] = defaultdict(list)
    domain_hits: dict[str, int] = defaultdict(int)
    unique_dom_per_user: list[int] = []

    items_meta_path = Path(cfg["paths"]["processed_dir"]) / "items.parquet"
    items = pd.read_parquet(items_meta_path)
    domain_by_key = items.set_index("item_key")["domain"].astype(str).to_dict()
    pop_by_key = items.set_index("item_key")["popularity"].fillna(0).astype(float).to_dict()

    coverage_items: set[str] = set()
    novelty_scores: list[float] = []

    users_evaluated = 0
    for _uid, part in val_df.groupby("user_id"):
        part = part.sort_values("score", ascending=False).head(cap)
        rel = part["label"].to_numpy(dtype=float)
        if rel.sum() == 0:
            continue
        users_evaluated += 1

        for k in ks:
            ndcgs[k].append(ndcg_at_k(rel, k))
            recalls[k].append(recall_at_k(rel, k))
            maps[k].append(average_precision_at_k(rel, k))

        topk = part.head(k_max)
        doms = {domain_by_key[str(ik)] for ik in topk["item_key"] if str(ik) in domain_by_key}
        unique_dom_per_user.append(len(doms))

        for ik in topk["item_key"]:
            ik = str(ik)
            domain_hits[domain_by_key.get(ik, "unknown")] += 1

        for ik in topk["item_key"]:
            ik = str(ik)
            coverage_items.add(ik)
            p = float(pop_by_key.get(ik, 0.0))
            novelty_scores.append(float(-np.log1p(max(p, 0.0))))

    total_dom_hits = sum(domain_hits.values()) or 1
    cross_dom_ratio = 1.0 - (domain_hits.get("movie", 0) / total_dom_hits)

    metrics: dict[str, float | int] = {
        "val_users_evaluated": users_evaluated,
        "cross_domain_fraction_non_movie": float(cross_dom_ratio),
        "avg_unique_domains_topk": float(np.mean(unique_dom_per_user)) if unique_dom_per_user else 0.0,
    }
    for k in ks:
        metrics[f"ndcg@{k}"] = float(np.mean(ndcgs[k])) if ndcgs[k] else 0.0
        metrics[f"recall@{k}"] = float(np.mean(recalls[k])) if recalls[k] else 0.0
        metrics[f"map@{k}"] = float(np.mean(maps[k])) if maps[k] else 0.0

    n_items = len(items)
    metrics[f"coverage@{k_max}"] = len(coverage_items) / n_items if n_items else 0.0
    metrics["novelty_mean_neg_log_pop"] = float(np.mean(novelty_scores)) if novelty_scores else 0.0

    out_path = art_dir / "eval_metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
