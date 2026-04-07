from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def default_db_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "tracker.sqlite3"


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            anxiety_level REAL NOT NULL,
            sleep_hours REAL,
            caffeine_mg REAL,
            heart_rate_bpm REAL,
            breathing_rate_bpm REAL,
            stress_event TEXT,
            context TEXT,
            food_level REAL
        );
        CREATE INDEX IF NOT EXISTS idx_checkins_user_ts ON checkins(user_id, ts);

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ts TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_episodes_user_ts ON episodes(user_id, ts);
        """
    )


def init_db(db_path: Path | None = None) -> Path:
    path = db_path or default_db_path()
    with connect(path) as conn:
        migrate(conn)
    return path


def insert_checkin(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    ts: str,
    anxiety_level: float,
    sleep_hours: float | None = None,
    caffeine_mg: float | None = None,
    heart_rate_bpm: float | None = None,
    breathing_rate_bpm: float | None = None,
    stress_event: str = "",
    context: str = "",
    food_level: float | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO checkins(
            user_id, ts, anxiety_level, sleep_hours, caffeine_mg,
            heart_rate_bpm, breathing_rate_bpm, stress_event, context, food_level
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id,
            ts,
            anxiety_level,
            sleep_hours,
            caffeine_mg,
            heart_rate_bpm,
            breathing_rate_bpm,
            stress_event or "",
            context or "",
            food_level,
        ),
    )
    return int(cur.lastrowid)


def insert_episode(conn: sqlite3.Connection, *, user_id: str, ts: str) -> int:
    cur = conn.execute(
        "INSERT INTO episodes(user_id, ts) VALUES (?,?)",
        (user_id, ts),
    )
    return int(cur.lastrowid)


def fetch_checkins(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM checkins ORDER BY user_id, ts"
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_episodes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM episodes ORDER BY user_id, ts"
    ).fetchall()
    return [dict(r) for r in rows]
