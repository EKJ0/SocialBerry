from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import Any

import joblib
import numpy as np

from tracker.features import row_to_vector
from tracker.inputs_user import UserCheckIn

MODEL_DIR = Path(__file__).resolve().parent / "models"


def prob_to_level(p: float) -> str:
    if p < 0.28:
        return "low"
    if p < 0.55:
        return "medium"
    return "high"


def _predict_proba_positive(bundle: dict, X: np.ndarray) -> float:
    if bundle["kind"] == "constant":
        return float(bundle["p_positive"])
    pipe = bundle["pipeline"]
    proba = pipe.predict_proba(X)
    # class 1 is positive episode risk
    if proba.shape[1] == 1:
        return float(proba[0, 0])
    return float(proba[0, 1])


class RiskPredictor:
    """Loads trained joblib bundles and scores a single check-in."""

    def __init__(self, models_dir: Path | None = None) -> None:
        root = models_dir or MODEL_DIR
        self._hour = joblib.load(root / "model_next_hour.joblib")
        self._day = joblib.load(root / "model_next_day.joblib")

    def predict_row(self, row: dict[str, Any]) -> dict[str, Any]:
        X = row_to_vector(row).reshape(1, -1)
        p1 = _predict_proba_positive(self._hour, X)
        p24 = _predict_proba_positive(self._day, X)
        return {
            "risk_next_hour": {
                "level": prob_to_level(p1),
                "probability_episode": round(p1, 4),
                "note": "Not a prediction of an exact time; short-horizon risk estimate.",
            },
            "risk_next_day": {
                "level": prob_to_level(p24),
                "probability_episode": round(p24, 4),
                "note": "Not a diagnosis; 24h horizon risk estimate.",
            },
        }


def predict_from_dict(d: dict[str, Any]) -> dict[str, Any]:
    ci = UserCheckIn(
        anxiety_level=float(d["anxiety_level"]),
        sleep_hours=d.get("sleep_hours"),
        caffeine_mg=d.get("caffeine_mg"),
        heart_rate_bpm=d.get("heart_rate_bpm"),
        breathing_rate_bpm=d.get("breathing_rate_bpm"),
        stress_event=d.get("stress_event") or "",
        context=d.get("context") or "",
        food_level=d.get("food_level"),
        hours_since_last_episode=d.get("hours_since_last_episode"),
    )
    row = ci.to_feature_dict()
    return RiskPredictor().predict_row(row)


def models_ready() -> bool:
    return (MODEL_DIR / "model_next_hour.joblib").exists() and (MODEL_DIR / "model_next_day.joblib").exists()


if __name__ == "__main__":
    import json
    import sys

    if not models_ready():
        print("Models not found. Run: python -m tracker.train", file=sys.stderr)
        sys.exit(1)
    sample = {
        "anxiety_level": 7,
        "sleep_hours": 5.0,
        "caffeine_mg": 200,
        "heart_rate_bpm": 98,
        "breathing_rate_bpm": 22,
        "stress_event": "deadline",
        "context": "work",
        "food_level": 3,
        "hours_since_last_episode": 48,
    }
    print(json.dumps(predict_from_dict(sample), indent=2))
