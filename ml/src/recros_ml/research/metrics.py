from __future__ import annotations

import numpy as np


def ranking_metrics(ranked: list[int], relevant: set[int], k: int) -> dict[str, float]:
    if len(ranked) != len(set(ranked)):
        raise ValueError("Ranking contains duplicate IDs")
    if k <= 0:
        raise ValueError("k must be positive")
    hits = np.array([item in relevant for item in ranked[:k]], dtype=float)
    ideal = sum(1 / np.log2(i + 2) for i in range(min(k, len(relevant))))
    dcg = float(np.sum(hits / np.log2(np.arange(len(hits)) + 2)))
    ap_sum = float(np.sum(hits * np.cumsum(hits) / (np.arange(len(hits)) + 1)))
    return {"ndcg": dcg / ideal if ideal else 0.0,
            "recall": float(hits.sum()) / len(relevant) if relevant else 0.0,
            "map": ap_sum / min(k, len(relevant)) if relevant else 0.0,
            "precision": float(hits.sum()) / k}


def bootstrap_mean(values: list[float], seed: int = 42, samples: int = 2000) -> dict:
    x = np.asarray(values, dtype=float)
    if not len(x):
        return {"mean": None, "ci95": [None, None], "n": 0}
    rng = np.random.default_rng(seed)
    estimates = x[rng.integers(0, len(x), (samples, len(x)))].mean(axis=1)
    return {"mean": float(x.mean()), "ci95": np.quantile(estimates, [.025, .975]).tolist(), "n": len(x)}


def exposure_gini(counts: np.ndarray) -> float:
    x = np.sort(np.asarray(counts, dtype=float))
    if not x.sum():
        return 0.0
    n = len(x)
    return float(2 * np.dot(np.arange(1, n + 1), x) / (n * x.sum()) - (n + 1) / n)
