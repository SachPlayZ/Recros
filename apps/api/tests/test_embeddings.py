from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from recros_api import db, embeddings
from recros_api.recommender import recommend, update_profile


class EmbeddingRecommendationTest(unittest.TestCase):
    def test_semantic_signal_ranks_cross_domain_match(self) -> None:
        old_db = db.DB_PATH
        old_bundle = os.environ.get("RECROS_RANKER_BUNDLE")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                db.DB_PATH = root / "test.db"
                bundle = root / "bundle"
                bundle.mkdir()
                np.save(
                    bundle / "embeddings.npy",
                    np.asarray([[1.0, 0.0], [0.98, 0.02], [0.0, 1.0]], dtype=np.float32),
                )
                (bundle / "item_keys.json").write_text(json.dumps(["movie:1", "book:1", "music:1"]))
                (bundle / "embedding_manifest.json").write_text(json.dumps({"model": "test", "provider": "local"}))
                os.environ["RECROS_RANKER_BUNDLE"] = str(bundle)
                embeddings._INDEX = None
                embeddings._MTIME = None
                db.init_db()
                with db.get_conn() as conn:
                    conn.executemany(
                        """INSERT INTO items
                           (id, domain, title, description, creators, genres, tags, year, popularity, rating, image_url, metadata)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        [
                            ("movie:1", "movie", "Space Film", "", "", "Science Fiction", "", 2020, 100, 4.5, "", "{}"),
                            ("book:1", "book", "Space Novel", "", "", "", "", 2020, 1, 3.0, "", "{}"),
                            ("music:1", "music", "Dance Song", "", "", "", "", 2020, 100, 3.0, "", "{}"),
                        ],
                    )
                user_id, _token = db.create_user()
                update_profile(user_id, {"seed_item_ids": ["movie:1"], "exploration": 0.5})
                result = recommend(user_id, limit=2)
                self.assertEqual(result[0]["id"], "book:1")
                self.assertIn("Semantically", result[0]["reason"])
        finally:
            db.DB_PATH = old_db
            embeddings._INDEX = None
            embeddings._MTIME = None
            if old_bundle is None:
                os.environ.pop("RECROS_RANKER_BUNDLE", None)
            else:
                os.environ["RECROS_RANKER_BUNDLE"] = old_bundle


if __name__ == "__main__":
    unittest.main()
