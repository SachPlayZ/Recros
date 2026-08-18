from __future__ import annotations

import os
import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = Path(os.getenv("RECROS_DB", ROOT / "apps" / "api" / "data" / "recros.db"))


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                preferred_domains TEXT NOT NULL DEFAULT '[]',
                genres TEXT NOT NULL DEFAULT '[]',
                themes TEXT NOT NULL DEFAULT '[]',
                moods TEXT NOT NULL DEFAULT '[]',
                disliked_terms TEXT NOT NULL DEFAULT '[]',
                exploration REAL NOT NULL DEFAULT 0.5,
                seed_item_ids TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL CHECK(domain IN ('movie', 'music', 'book')),
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                creators TEXT NOT NULL DEFAULT '',
                genres TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                year REAL,
                popularity REAL NOT NULL DEFAULT 0,
                rating REAL,
                image_url TEXT NOT NULL DEFAULT '',
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
                action TEXT NOT NULL CHECK(action IN ('like', 'dislike', 'save', 'skip', 'consume')),
                value REAL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_items_domain ON items(domain);
            CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id, created_at);
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
        migrations = {
            "email": "ALTER TABLE users ADD COLUMN email TEXT",
            "password_hash": "ALTER TABLE users ADD COLUMN password_hash TEXT",
            "auth_token_hash": "ALTER TABLE users ADD COLUMN auth_token_hash TEXT",
            "token_created_at": "ALTER TABLE users ADD COLUMN token_created_at TEXT",
        }
        for name, statement in migrations.items():
            if name not in columns:
                conn.execute(statement)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return f"pbkdf2_sha256$240000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded or not encoded.startswith("pbkdf2_sha256$"):
        return False
    _, rounds, salt_hex, expected = encoded.split("$", 3)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds))
    return secrets.compare_digest(digest.hex(), expected)


def create_user(email: str | None = None, password: str | None = None) -> tuple[int, str]:
    token = secrets.token_urlsafe(32)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users(created_at, email, password_hash, auth_token_hash, token_created_at) VALUES (?, ?, ?, ?, ?)",
            (utc_now(), email, _hash_password(password) if password else None, _hash_token(token), utc_now()),
        )
        user_id = int(cur.lastrowid)
        conn.execute("INSERT INTO profiles(user_id, updated_at) VALUES (?, ?)", (user_id, utc_now()))
        return user_id, token


def user_exists(user_id: int) -> bool:
    with get_conn() as conn:
        return conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is not None


def authenticate_token(token: str) -> int | None:
    token_hash = _hash_token(token)
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE auth_token_hash = ?", (token_hash,)).fetchone()
    return int(row["id"]) if row else None


def authenticate_password(email: str, password: str) -> tuple[int, str] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            return None
        token = secrets.token_urlsafe(32)
        conn.execute(
            "UPDATE users SET auth_token_hash = ?, token_created_at = ? WHERE id = ?",
            (_hash_token(token), utc_now(), row["id"]),
        )
        return int(row["id"]), token


def revoke_token(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE users SET auth_token_hash = NULL, token_created_at = NULL WHERE id = ?", (user_id,))


def email_exists(email: str) -> bool:
    with get_conn() as conn:
        return conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() is not None
