from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def get_db_path(base_dir: Path) -> Path:
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "plantme.sqlite3"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_conn(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL CHECK(role IN ('client', 'trustablePerson')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('client', 'trustablePerson')),
            code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_auth_codes_identifier_created
        ON auth_codes(identifier, created_at);

        CREATE TABLE IF NOT EXISTS invites (
            code TEXT PRIMARY KEY,
            client_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            used_by_user_id INTEGER,
            FOREIGN KEY(client_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(used_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS pairings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_user_id INTEGER NOT NULL,
            trusted_user_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','accepted')),
            created_at TEXT NOT NULL,
            accepted_at TEXT,
            UNIQUE(client_user_id, trusted_user_id),
            FOREIGN KEY(client_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(trusted_user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS onboarding_answers (
            user_id INTEGER PRIMARY KEY,
            answers_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS share_settings (
            pairing_id INTEGER PRIMARY KEY,
            fields_allowed_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(pairing_id) REFERENCES pairings(id) ON DELETE CASCADE
        );
        """
    )


def fetch_one(conn: sqlite3.Connection, query: str, args: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    cur = conn.execute(query, args)
    return cur.fetchone()


def fetch_all(conn: sqlite3.Connection, query: str, args: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    cur = conn.execute(query, args)
    return list(cur.fetchall())

