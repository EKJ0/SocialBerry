from __future__ import annotations

# Allow `python tracker/train.py` from repo root (Windows-friendly).
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse
import json
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from tracker.db import connect, fetch_checkins, fetch_episodes, init_db, migrate
from tracker.features import FEATURE_NAMES, rows_to_matrix
from tracker.labels import enrich_checkin_row, labels_for_checkin
from tracker.synthetic import generate_synthetic_dataset

MODEL_DIR = Path(__file__).resolve().parent / "models"


def prob_to_level(p: float) -> str:
    if p < 0.28:
        return "low"
    if p < 0.55:
        return "medium"
    return "high"


def build_xy(
    checkins: list[dict[str, Any]], episodes: list[dict[str, Any]]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = [enrich_checkin_row(c, episodes) for c in checkins]
    y1_list: list[int] = []
    y24_list: list[int] = []
    for c in checkins:
        y1, y24 = labels_for_checkin(c, episodes)
        y1_list.append(y1)
        y24_list.append(y24)
    X = rows_to_matrix(rows)
    return X, np.array(y1_list, dtype=np.int32), np.array(y24_list, dtype=np.int32)


def fit_or_constant(y: np.ndarray, X: np.ndarray) -> dict:
    if X.shape[0] == 0:
        return {"kind": "constant", "p_positive": 0.12}
    uniq = set(int(v) for v in y.tolist())
    if len(uniq) < 2:
        rate = float(np.mean(y)) if y.size else 0.0
        return {"kind": "constant", "p_positive": max(0.02, min(0.85, rate or 0.12))}
    pipe = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=800,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    pipe.fit(X, y)
    return {"kind": "sklearn", "pipeline": pipe, "feature_names": FEATURE_NAMES}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train risk models (next 1h / next 24h).")
    parser.add_argument("--db", type=Path, default=None, help="SQLite path (default tracker/data/tracker.sqlite3)")
    parser.add_argument("--synthetic-only", action="store_true", help="Ignore DB; train on synthetic data only")
    parser.add_argument(
        "--real-only",
        action="store_true",
        help="Do not merge synthetic data (needs enough real check-ins or training may degrade)",
    )
    args = parser.parse_args()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    checkins: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []

    if not args.synthetic_only:
        db_path = init_db(args.db)
        with connect(db_path) as conn:
            migrate(conn)
            checkins = fetch_checkins(conn)
            episodes = fetch_episodes(conn)

    if args.synthetic_only:
        s_chk, s_ep = generate_synthetic_dataset()
        checkins = s_chk
        episodes = s_ep
    elif not args.real_only and len(checkins) < 80:
        s_chk, s_ep = generate_synthetic_dataset()
        checkins = checkins + s_chk
        episodes = episodes + s_ep

    if len(checkins) < 30 and not args.real_only and not args.synthetic_only:
        s_chk, s_ep = generate_synthetic_dataset()
        checkins.extend(s_chk)
        episodes.extend(s_ep)

    X, y1, y24 = build_xy(checkins, episodes)

    model_hour = fit_or_constant(y1, X)
    model_day = fit_or_constant(y24, X)

    joblib.dump(model_hour, MODEL_DIR / "model_next_hour.joblib")
    joblib.dump(model_day, MODEL_DIR / "model_next_day.joblib")

    meta = {
        "n_checkins": len(checkins),
        "n_episodes": len(episodes),
        "y1_positive_rate": float(np.mean(y1)) if y1.size else 0.0,
        "y24_positive_rate": float(np.mean(y24)) if y24.size else 0.0,
        "feature_count": int(X.shape[1]) if X.size else 0,
    }
    (MODEL_DIR / "train_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Saved models to", MODEL_DIR)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
