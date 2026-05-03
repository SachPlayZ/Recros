from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    """Recros repo root (directory containing ``ml/``)."""
    return Path(__file__).resolve().parents[3]


def ml_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path).resolve()
    raw = yaml.safe_load(path.read_text())
    root = repo_root()
    paths = raw.setdefault("paths", {})
    for key in ("processed_dir", "features_dir", "artifacts_dir"):
        if key in paths:
            paths[key] = str((root / paths[key]).resolve())
    ds = raw.setdefault("datasets", {})
    for key, rel in list(ds.items()):
        if isinstance(rel, str):
            ds[key] = str((root / rel).resolve())
    raw["_config_path"] = str(path)
    raw["_repo_root"] = str(root)
    return raw
