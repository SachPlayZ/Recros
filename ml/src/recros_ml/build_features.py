from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from recros_ml.config import load_config
from recros_ml.features.builder import build_training_frame
from recros_ml.logging_setup import add_log_arguments, setup_logging_args

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build supervised training pairs and tabular features.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    add_log_arguments(parser)
    args = parser.parse_args()
    setup_logging_args(args)

    cfg = load_config(args.config)
    feat_dir = Path(cfg["paths"]["features_dir"])
    feat_dir.mkdir(parents=True, exist_ok=True)

    df, feature_cols = build_training_frame(cfg)
    out_parquet = feat_dir / "train_pairs.parquet"
    log.info("Writing %s ...", out_parquet)
    df.to_parquet(out_parquet, index=False)
    (feat_dir / "feature_columns.json").write_text(json.dumps(feature_cols, indent=2))

    pos_rate = float(df["label"].mean()) if len(df) else 0.0
    log.info(
        "Done: %s rows, %s features, positive_rate=%.4f -> %s",
        len(df),
        len(feature_cols),
        pos_rate,
        out_parquet,
    )


if __name__ == "__main__":
    main()
