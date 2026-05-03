from __future__ import annotations

import argparse
from pathlib import Path

from recros_ml.config import load_config
from recros_ml.ingest.loaders import build_all_tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Kaggle CSVs into unified parquet tables.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    out_dir = Path(cfg["paths"]["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    items, users, interactions = build_all_tables(cfg)
    items.to_parquet(out_dir / "items.parquet", index=False)
    users.to_parquet(out_dir / "users.parquet", index=False)
    interactions.to_parquet(out_dir / "interactions.parquet", index=False)

    print(f"Wrote {len(items)} items, {len(users)} users, {len(interactions)} interactions -> {out_dir}")


if __name__ == "__main__":
    main()
