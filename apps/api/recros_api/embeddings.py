from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BUNDLE = ROOT / "ml" / "artifacts" / "bundle_latest"


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return vector / max(norm, 1e-12)


class EmbeddingIndex:
    def __init__(self, bundle_dir: Path):
        self.bundle_dir = bundle_dir.resolve()
        self.matrix = np.load(self.bundle_dir / "embeddings.npy", mmap_mode="r")
        self.item_keys = json.loads((self.bundle_dir / "item_keys.json").read_text())
        if self.matrix.ndim != 2 or len(self.item_keys) != self.matrix.shape[0]:
            raise RuntimeError("Embedding artifact shape does not match item keys")
        self.row_by_item = {str(key): index for index, key in enumerate(self.item_keys)}
        manifest_path = self.bundle_dir / "embedding_manifest.json"
        self.manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    def profile_vector(self, item_ids: list[str]) -> np.ndarray | None:
        vectors = [self.matrix[self.row_by_item[item_id]] for item_id in item_ids if item_id in self.row_by_item]
        if not vectors:
            return None
        return _normalize(np.mean(np.asarray(vectors, dtype=np.float32), axis=0))

    def scores(self, rows: list[Any], profile_item_ids: list[str]) -> np.ndarray:
        profile = self.profile_vector(profile_item_ids)
        scores = np.zeros(len(rows), dtype=np.float32)
        if profile is None:
            return scores
        for index, row in enumerate(rows):
            item_index = self.row_by_item.get(str(row["id"]))
            if item_index is not None:
                scores[index] = float(np.dot(profile, self.matrix[item_index]))
        return scores

    def status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "bundle": str(self.bundle_dir),
            "model": self.manifest.get("model", "unknown"),
            "provider": self.manifest.get("provider", "unknown"),
            "dimensions": int(self.matrix.shape[1]),
            "items": int(self.matrix.shape[0]),
        }


_INDEX: EmbeddingIndex | None = None
_ERROR: str | None = None
_MTIME: int | None = None


def get_embedding_index() -> EmbeddingIndex | None:
    global _INDEX, _ERROR, _MTIME
    bundle = Path(os.getenv("RECROS_RANKER_BUNDLE", str(DEFAULT_BUNDLE)))
    matrix_path = bundle / "embeddings.npy"
    if not matrix_path.exists():
        _ERROR = f"embedding artifact not found: {bundle}"
        return None
    mtime = matrix_path.stat().st_mtime_ns
    if _INDEX is not None and _MTIME == mtime:
        return _INDEX
    try:
        _INDEX = EmbeddingIndex(bundle)
        _MTIME = mtime
        _ERROR = None
    except Exception as exc:  # pragma: no cover - exercised by broken deployment artifacts.
        _ERROR = str(exc)
        _INDEX = None
    return _INDEX


def embedding_status() -> dict[str, Any]:
    index = get_embedding_index()
    if index is None:
        return {"enabled": False, "error": _ERROR}
    return index.status()
