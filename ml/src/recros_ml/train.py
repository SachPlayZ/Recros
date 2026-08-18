from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from recros_ml.config import load_config
from recros_ml.logging_setup import add_log_arguments, setup_logging_args

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train LightGBM binary ranker on engineered pairs.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    add_log_arguments(parser)
    args = parser.parse_args()
    setup_logging_args(args)

    cfg = load_config(args.config)
    feat_dir = Path(cfg["paths"]["features_dir"])
    art_dir = Path(cfg["paths"]["artifacts_dir"])
    art_dir.mkdir(parents=True, exist_ok=True)

    log_cfg = cfg.get("logging") or {}
    eval_period = int(log_cfg.get("lightgbm_eval_period", 10))

    log.info("Loading train_pairs.parquet from %s", feat_dir)
    df = pd.read_parquet(feat_dir / "train_pairs.parquet")
    feature_cols: list[str] = json.loads((feat_dir / "feature_columns.json").read_text())
    log.info("Loaded rows=%s features=%s", len(df), len(feature_cols))

    users = df["user_id"].unique()
    rng = np.random.RandomState(int(cfg["split"]["random_seed"]))
    val_frac = float(cfg["split"]["val_user_fraction"])
    n_val = max(1, int(len(users) * val_frac))
    val_users = set(rng.choice(users, size=n_val, replace=False))

    train_mask = ~df["user_id"].isin(val_users)
    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, "label"].astype(int)
    X_val = df.loc[~train_mask, feature_cols]
    y_val = df.loc[~train_mask, "label"].astype(int)

    log.info("Train rows=%s val rows=%s val_users=%s", len(X_train), len(X_val), n_val)

    train_ds = lgb.Dataset(X_train, label=y_train)
    val_ds = lgb.Dataset(X_val, label=y_val, reference=train_ds)

    lgb_cfg = {k: v for k, v in cfg["lightgbm"].items()}
    num_round = int(lgb_cfg.pop("num_boost_round", 500))
    early = int(lgb_cfg.pop("early_stopping_rounds", 50))

    callbacks = [
        lgb.early_stopping(stopping_rounds=early, verbose=False),
        lgb.log_evaluation(period=eval_period),
    ]

    log.info("Starting LightGBM (boost_round=%s early_stopping=%s eval_period=%s)...", num_round, early, eval_period)
    model = lgb.train(
        lgb_cfg,
        train_ds,
        num_boost_round=num_round,
        valid_sets=[val_ds],
        valid_names=["val"],
        callbacks=callbacks,
    )

    model_path = art_dir / "ranker_lgb.txt"
    model.save_model(str(model_path))

    best_it = model.best_iteration
    if best_it is None or best_it <= 0:
        best_it = model.current_iteration()

    val_pred = model.predict(X_val, num_iteration=best_it)
    try:
        val_auc = float(roc_auc_score(y_val, val_pred))
    except ValueError:
        val_auc = float("nan")

    meta = {
        "best_iteration": int(best_it),
        "val_rows": int(len(X_val)),
        "train_rows": int(len(X_train)),
        "val_binary_auc": val_auc,
        "feature_count": len(feature_cols),
    }
    items = pd.read_parquet(Path(cfg["paths"]["processed_dir"]) / "items.parquet")
    year_values = items["year"].dropna()
    movie_ratings = items.loc[items["domain"] == "movie", "avg_rating"].dropna()
    meta["feature_defaults"] = {
        "year": float(np.nanmedian(year_values)) if len(year_values) else 2000.0,
        "rating_item": float(np.nanmedian(movie_ratings)) if len(movie_ratings) else 3.5,
    }
    (art_dir / "train_meta.json").write_text(json.dumps(meta, indent=2))
    (art_dir / "val_users.json").write_text(json.dumps(sorted(int(u) for u in val_users)))

    log.info("Saved model -> %s (best_iteration=%s val_AUC=%.4f)", model_path, best_it, val_auc)


if __name__ == "__main__":
    main()
