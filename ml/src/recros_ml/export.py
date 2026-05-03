from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from recros_ml.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Bundle model, schema, and metrics for deployment.")
    parser.add_argument("--config", type=str, default="ml/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    art_dir = Path(cfg["paths"]["artifacts_dir"])
    feat_dir = Path(cfg["paths"]["features_dir"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = art_dir / f"bundle_{stamp}"
    bundle.mkdir(parents=True, exist_ok=True)

    copies = [
        (art_dir / "ranker_lgb.txt", bundle / "ranker_lgb.txt"),
        (feat_dir / "feature_columns.json", bundle / "feature_columns.json"),
        (art_dir / "train_meta.json", bundle / "train_meta.json"),
        (art_dir / "eval_metrics.json", bundle / "eval_metrics.json"),
        (art_dir / "val_users.json", bundle / "val_users.json"),
    ]
    for src, dst in copies:
        if src.exists():
            shutil.copy2(src, dst)

    manifest = {
        "version": stamp,
        "created_utc": stamp,
        "repo_root": cfg["_repo_root"],
        "config_path": cfg["_config_path"],
        "files": [p.name for _, p in copies if p.exists()],
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2))

    latest = art_dir / "bundle_latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            shutil.rmtree(latest)
    try:
        latest.symlink_to(bundle.name, target_is_directory=True)
    except OSError:
        shutil.copytree(bundle, latest)

    print(f"Exported bundle -> {bundle}")


if __name__ == "__main__":
    main()
