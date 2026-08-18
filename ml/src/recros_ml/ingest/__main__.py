from __future__ import annotations

import argparse
import logging
from pathlib import Path

from recros_ml.config import load_config
from recros_ml.ingest.loaders import build_all_tables
from recros_ml.logging_setup import add_log_arguments, setup_logging_args

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Kaggle CSVs into unified parquet tables.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    add_log_arguments(parser)
    args = parser.parse_args()
    setup_logging_args(args)

    cfg = load_config(args.config)
    out_dir = Path(cfg["paths"]["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Writing parquet under %s", out_dir)
    items, users, interactions = build_all_tables(cfg)
    log.info("Saving items.parquet (%s rows)...", len(items))
    items.to_parquet(out_dir / "items.parquet", index=False)
    log.info("Saving users.parquet (%s rows)...", len(users))
    users.to_parquet(out_dir / "users.parquet", index=False)
    log.info("Saving interactions.parquet (%s rows)...", len(interactions))
    interactions.to_parquet(out_dir / "interactions.parquet", index=False)

    log.info(
        "Done: %s items, %s users, %s interactions -> %s",
        len(items),
        len(users),
        len(interactions),
        out_dir,
    )


if __name__ == "__main__":
    main()
