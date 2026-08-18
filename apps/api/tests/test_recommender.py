from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from recros_api import db
from recros_api.recommender import recommend, record_event, update_profile


class RecommenderTest(unittest.TestCase):
    def test_profile_and_feedback_signals_change_results(self) -> None:
        old_path = db.DB_PATH
        with tempfile.TemporaryDirectory() as temp_dir:
            db.DB_PATH = Path(temp_dir) / "test.db"
            db.init_db()
            with db.get_conn() as conn:
                conn.executemany(
                    """INSERT INTO items
                       (id, domain, title, description, creators, genres, tags, year, popularity, rating, image_url, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        ("movie:1", "movie", "Quiet Space", "A thoughtful journey", "", "Science Fiction", "", 2020, 10, 4.5, "", "{}"),
                        ("book:1", "book", "Loud Romance", "A romantic story", "", "Romance", "", 2020, 10, 4.5, "", "{}"),
                    ],
                )
            user_id, _token = db.create_user()
            update_profile(user_id, {"preferred_domains": ["movie"], "genres": ["Science Fiction"], "exploration": 0.2})
            results = recommend(user_id, limit=1)
            self.assertEqual(results[0]["id"], "movie:1")
            record_event(user_id, "movie:1", "skip")
            self.assertEqual(recommend(user_id, limit=1)[0]["id"], "book:1")
        db.DB_PATH = old_path


if __name__ == "__main__":
    unittest.main()
