"""
One-shot demo: load sample data into SQLite, train models (--real-only), print sample prediction.

From repo root:
  python -m tracker.run_demo
  python tracker/run_demo.py

Append without clearing DB:
  python -m tracker.run_demo --append
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Tracker demo: load, train, predict.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Keep existing DB rows (default: clear checkins/episodes before sample load)",
    )
    args = parser.parse_args()

    from tracker.db import connect, init_db, insert_checkin, insert_episode, migrate
    from tracker.synthetic import generate_synthetic_dataset

    init_db()
    # Enough rows to train without merging extra synthetic (>= 80 check-ins).
    checkins, episodes = generate_synthetic_dataset(n_users=4, checkins_per_user=28, seed=99)

    with connect() as conn:
        migrate(conn)
        if not args.append:
            conn.execute("DELETE FROM checkins")
            conn.execute("DELETE FROM episodes")
        for c in checkins:
            insert_checkin(
                conn,
                user_id=c["user_id"],
                ts=c["ts"],
                anxiety_level=float(c["anxiety_level"]),
                sleep_hours=c.get("sleep_hours"),
                caffeine_mg=c.get("caffeine_mg"),
                heart_rate_bpm=c.get("heart_rate_bpm"),
                breathing_rate_bpm=c.get("breathing_rate_bpm"),
                stress_event=c.get("stress_event") or "",
                context=c.get("context") or "",
                food_level=c.get("food_level"),
            )
        for e in episodes:
            insert_episode(conn, user_id=e["user_id"], ts=e["ts"])

    db_path = _REPO_ROOT / "tracker" / "data" / "tracker.sqlite3"
    print(f"Loaded {len(checkins)} check-ins and {len(episodes)} episodes -> {db_path}", flush=True)
    print("Training with --real-only (no extra synthetic merge)...", flush=True)

    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    r = subprocess.run(
        [sys.executable, "-m", "tracker.train", "--real-only"],
        cwd=str(_REPO_ROOT),
        env=env,
    )
    if r.returncode != 0:
        sys.exit(r.returncode)

    print("\nSample prediction:", flush=True)
    r2 = subprocess.run(
        [sys.executable, "-m", "tracker.predict"],
        cwd=str(_REPO_ROOT),
        env=env,
    )
    sys.exit(r2.returncode)


if __name__ == "__main__":
    main()
