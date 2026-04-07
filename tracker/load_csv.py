"""
Load checkins + episodes from CSV into tracker SQLite.

Usage (from repo root):
  python -m tracker.load_csv --dir tracker/datasets
  python -m tracker.load_csv --checkins path/to/checkins.csv --episodes path/to/episodes.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import csv
import re
from typing import Any

from tracker.db import connect, init_db, insert_checkin, insert_episode, migrate

ALIASES: dict[str, tuple[str, ...]] = {
    "user_id": ("user_id", "user", "subject_id", "id_user", "participant_id"),
    "ts": ("ts", "timestamp", "datetime", "time", "date_time"),
    "anxiety_level": ("anxiety_level", "anxiety", "gad", "stress_level", "anxiety_score"),
    "sleep_hours": ("sleep_hours", "sleep", "sleep_hrs"),
    "caffeine_mg": ("caffeine_mg", "caffeine", "caffeine_mg_total"),
    "heart_rate_bpm": ("heart_rate_bpm", "hr", "heart_rate", "bpm"),
    "breathing_rate_bpm": ("breathing_rate_bpm", "br", "breathing_rate", "resp_rate", "rr"),
    "stress_event": ("stress_event", "stress_type", "stress", "stressor"),
    "context": ("context", "location", "place", "setting"),
    "food_level": ("food_level", "food", "hunger_inverse"),
}


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", "_", h.strip().lower())


def _map_headers(fieldnames: list[str] | None) -> dict[str, str]:
    """Map canonical name -> actual column name in CSV."""
    if not fieldnames:
        return {}
    lowered = {_norm_header(f): f for f in fieldnames}
    out: dict[str, str] = {}
    for canon, options in ALIASES.items():
        for opt in options:
            key = _norm_header(opt)
            if key in lowered:
                out[canon] = lowered[key]
                break
    return out


def _parse_float(v: Any) -> float | None:
    if v is None or (isinstance(v, str) and not str(v).strip()):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return list(fieldnames), rows


def load_checkins_csv(conn, path: Path) -> int:
    fieldnames, rows = _read_rows(path)
    cmap = _map_headers(fieldnames)
    if "user_id" not in cmap or "ts" not in cmap or "anxiety_level" not in cmap:
        missing = [k for k in ("user_id", "ts", "anxiety_level") if k not in cmap]
        raise ValueError(
            f"{path}: missing required columns (after alias match): {missing}. "
            f"Found headers: {fieldnames}"
        )
    n = 0
    for r in rows:
        uid = (r.get(cmap["user_id"]) or "").strip()
        ts = (r.get(cmap["ts"]) or "").strip()
        anx = _parse_float(r.get(cmap["anxiety_level"]))
        if not uid or not ts or anx is None:
            continue
        insert_checkin(
            conn,
            user_id=uid,
            ts=ts,
            anxiety_level=float(anx),
            sleep_hours=_parse_float(r.get(cmap["sleep_hours"])) if "sleep_hours" in cmap else None,
            caffeine_mg=_parse_float(r.get(cmap["caffeine_mg"])) if "caffeine_mg" in cmap else None,
            heart_rate_bpm=_parse_float(r.get(cmap["heart_rate_bpm"])) if "heart_rate_bpm" in cmap else None,
            breathing_rate_bpm=_parse_float(r.get(cmap["breathing_rate_bpm"])) if "breathing_rate_bpm" in cmap else None,
            stress_event=(r.get(cmap["stress_event"]) or "").strip() if "stress_event" in cmap else "",
            context=(r.get(cmap["context"]) or "").strip() if "context" in cmap else "",
            food_level=_parse_float(r.get(cmap["food_level"])) if "food_level" in cmap else None,
        )
        n += 1
    return n


def load_episodes_csv(conn, path: Path) -> int:
    fieldnames, rows = _read_rows(path)
    cmap = _map_headers(fieldnames)
    if "user_id" not in cmap or "ts" not in cmap:
        raise ValueError(f"{path}: need user_id and ts (or aliases). Found: {fieldnames}")
    n = 0
    for r in rows:
        uid = (r.get(cmap["user_id"]) or "").strip()
        ts = (r.get(cmap["ts"]) or "").strip()
        if not uid or not ts:
            continue
        insert_episode(conn, user_id=uid, ts=ts)
        n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser(description="Import tracker CSVs into SQLite.")
    p.add_argument("--dir", type=Path, default=None, help="Folder containing checkins.csv and optionally episodes.csv")
    p.add_argument("--checkins", type=Path, default=None, help="Path to checkins.csv")
    p.add_argument("--episodes", type=Path, default=None, help="Path to episodes.csv")
    p.add_argument("--replace", action="store_true", help="Clear checkins and episodes before import")
    p.add_argument("--db", type=Path, default=None, help="Override SQLite path")
    args = p.parse_args()

    checkins_path = args.checkins
    episodes_path = args.episodes
    if args.dir:
        d = args.dir
        if checkins_path is None:
            checkins_path = d / "checkins.csv"
        if episodes_path is None:
            episodes_path = d / "episodes.csv"

    if checkins_path is None or not checkins_path.is_file():
        raise SystemExit(
            "Need --checkins FILE or --dir DIR with checkins.csv inside.\n"
            "See tracker/datasets/README.md for column names."
        )

    db_path = init_db(args.db)
    with connect(db_path) as conn:
        migrate(conn)
        if args.replace:
            conn.execute("DELETE FROM checkins")
            conn.execute("DELETE FROM episodes")
        n_c = load_checkins_csv(conn, checkins_path)
        n_e = 0
        if episodes_path and episodes_path.is_file():
            n_e = load_episodes_csv(conn, episodes_path)
        elif episodes_path and not episodes_path.is_file():
            print(f"No episodes file at {episodes_path} — skipped.")

    print(f"Imported {n_c} checkins, {n_e} episodes into {db_path}")


if __name__ == "__main__":
    main()
