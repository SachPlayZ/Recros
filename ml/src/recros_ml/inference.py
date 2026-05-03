from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd


@dataclass
class RankerInference:
    """Loads exported LightGBM artifacts and scores candidate feature rows."""

    model: lgb.Booster
    feature_columns: list[str]
    best_iteration: int

    @classmethod
    def from_bundle(cls, bundle_dir: str | Path) -> RankerInference:
        root = Path(bundle_dir).resolve()
        model = lgb.Booster(model_file=str(root / "ranker_lgb.txt"))
        cols = json.loads((root / "feature_columns.json").read_text())
        meta = json.loads((root / "train_meta.json").read_text())
        bi = int(meta.get("best_iteration") or -1)
        return cls(model=model, feature_columns=cols, best_iteration=bi)

    def predict_frame(self, df: pd.DataFrame) -> np.ndarray:
        missing = set(self.feature_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing feature columns: {sorted(missing)}")
        X = df[self.feature_columns].astype(np.float32)
        return np.asarray(self.model.predict(X, num_iteration=self.best_iteration))

    def predict_dict_rows(self, rows: list[dict[str, Any]]) -> np.ndarray:
        df = pd.DataFrame(rows)
        return self.predict_frame(df)


def rank_candidates(item_features: pd.DataFrame, bundle_dir: str | Path) -> pd.DataFrame:
    """Returns ``item_features`` sorted by descending relevance score."""
    rk = RankerInference.from_bundle(bundle_dir)
    out = item_features.copy()
    out["score"] = rk.predict_frame(out)
    return out.sort_values("score", ascending=False).reset_index(drop=True)
