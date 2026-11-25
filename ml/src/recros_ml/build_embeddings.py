from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from recros_ml.config import load_config
from recros_ml.embeddings import content_hash, encode_texts, item_text
from recros_ml.logging_setup import add_log_arguments, setup_logging_args

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build versioned semantic item embeddings.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    parser.add_argument("--provider", choices=("local", "openai"), default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=64)
    add_log_arguments(parser)
    args = parser.parse_args()
    setup_logging_args(args)

    cfg = load_config(args.config)
    processed = Path(cfg["paths"]["processed_dir"])
    artifacts = Path(cfg["paths"]["artifacts_dir"])
    items = pd.read_parquet(processed / "items.parquet").drop_duplicates("item_key").reset_index(drop=True)
    keys = [str(value) for value in items["item_key"]]
    texts = [item_text(row) for _, row in items.iterrows()]
    embedding_cfg = cfg.get("embeddings") or {}
    provider = args.provider or str(embedding_cfg.get("provider", "local"))
    model_name = args.model or embedding_cfg.get("model")
    batch_size = max(1, int(args.batch_size or embedding_cfg.get("batch_size", 64)))

    log.info("Encoding %s items with provider=%s model=%s", len(items), provider, model_name or "default")
    matrix, resolved_model = encode_texts(texts, provider, model_name, batch_size)
    if len(matrix) != len(keys) or matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise RuntimeError("Embedding output shape/content is invalid")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = artifacts / f"embedding_bundle_{stamp}"
    bundle.mkdir(parents=True, exist_ok=True)
    np.save(bundle / "embeddings.npy", matrix.astype(np.float32))
    (bundle / "item_keys.json").write_text(json.dumps(keys, indent=2))
    manifest = {
        "version": stamp,
        "provider": provider,
        "model": resolved_model,
        "dimensions": int(matrix.shape[1]),
        "item_count": len(keys),
        "content_hash": content_hash(texts),
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2))

    latest = artifacts / "embedding_bundle_latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    try:
        latest.symlink_to(bundle.name, target_is_directory=True)
    except OSError:
        shutil.copytree(bundle, latest)
    log.info("Embedding bundle ready: %s shape=%s", bundle, matrix.shape)


if __name__ == "__main__":
    main()
