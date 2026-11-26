from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from recros_ml.config import load_config
from recros_ml.logging_setup import add_log_arguments, setup_logging_args

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a lightweight semantic embedding sanity evaluation.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    parser.add_argument("--sample-per-domain", type=int, default=100)
    add_log_arguments(parser)
    args = parser.parse_args()
    setup_logging_args(args)

    cfg = load_config(args.config)
    processed = Path(cfg["paths"]["processed_dir"])
    artifacts = Path(cfg["paths"]["artifacts_dir"])
    bundle = artifacts / "embedding_bundle_latest"
    matrix = np.load(bundle / "embeddings.npy", mmap_mode="r")
    keys = json.loads((bundle / "item_keys.json").read_text())
    items = pd.read_parquet(processed / "items.parquet").drop_duplicates("item_key").reset_index(drop=True)
    domains = items.set_index("item_key")["domain"].astype(str).to_dict()
    sample_keys: list[str] = []
    for domain in ("movie", "book", "music"):
        sample_keys.extend(
            items.loc[items["domain"] == domain, "item_key"].astype(str).head(max(1, args.sample_per_domain)).tolist()
        )
    row_by_key = {str(key): index for index, key in enumerate(keys)}
    cross_domain_hits = 0
    evaluated = 0
    for key in sample_keys:
        row = row_by_key.get(key)
        if row is None:
            continue
        scores = np.asarray(matrix @ matrix[row], dtype=np.float32)
        scores[row] = -np.inf
        top = np.argpartition(scores, -5)[-5:]
        if any(domains.get(str(keys[index])) != domains.get(key) for index in top):
            cross_domain_hits += 1
        evaluated += 1
    metrics = {
        "embedding_items": int(matrix.shape[0]),
        "embedding_dimensions": int(matrix.shape[1]),
        "sample_items": evaluated,
        "cross_domain_neighbor_hit@5": cross_domain_hits / evaluated if evaluated else 0.0,
    }
    (artifacts / "embedding_eval.json").write_text(json.dumps(metrics, indent=2))
    log.info("Embedding metrics: %s", json.dumps(metrics))


if __name__ == "__main__":
    main()
