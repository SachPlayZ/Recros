from __future__ import annotations

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from recros_ml.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Train LightGBM binary ranker on engineered pairs.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    feat_dir = Path(cfg["paths"]["features_dir"])
    art_dir = Path(cfg["paths"]["artifacts_dir"])
    art_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(feat_dir / "train_pairs.parquet")
    feature_cols: list[str] = json.loads((feat_dir / "feature_columns.json").read_text())

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

    train_ds = lgb.Dataset(X_train, label=y_train)
    val_ds = lgb.Dataset(X_val, label=y_val, reference=train_ds)

    lgb_cfg = {k: v for k, v in cfg["lightgbm"].items()}
    num_round = int(lgb_cfg.pop("num_boost_round", 500))
    early = int(lgb_cfg.pop("early_stopping_rounds", 50))

    callbacks = [
        lgb.early_stopping(stopping_rounds=early, verbose=False),
        lgb.log_evaluation(period=50),
    ]

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
    (art_dir / "train_meta.json").write_text(json.dumps(meta, indent=2))
    (art_dir / "val_users.json").write_text(json.dumps(sorted(val_users)))

    print(f"Saved model -> {model_path} (best_iteration={best_it}, val_AUC={val_auc:.4f})")


if __name__ == "__main__":
    main()
