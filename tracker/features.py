from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from tracker.inputs_user import CONTEXT_KEYS, STRESS_KEYS

# Fixed column order for sklearn
NUMERIC_KEYS = [
    "anxiety_level",
    "sleep_hours",
    "caffeine_mg",
    "heart_rate_bpm",
    "breathing_rate_bpm",
    "food_level",
    "hours_since_last_episode",
]
STRESS_COLS = [f"stress_{k or 'none'}" for k in STRESS_KEYS]
CONTEXT_COLS = [f"context_{k or 'none'}" for k in CONTEXT_KEYS]
FEATURE_NAMES = NUMERIC_KEYS + STRESS_COLS + CONTEXT_COLS


def _fill_num(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def row_to_vector(row: dict[str, Any]) -> np.ndarray:
    """Build feature vector from DB row or feature dict."""
    nums = [
        _fill_num(row.get("anxiety_level"), 0.0),
        _fill_num(row.get("sleep_hours"), 7.0),  # impute typical sleep if missing
        _fill_num(row.get("caffeine_mg"), 0.0),
        _fill_num(row.get("heart_rate_bpm"), 72.0),
        _fill_num(row.get("breathing_rate_bpm"), 16.0),
        _fill_num(row.get("food_level"), 5.0),
        _fill_num(row.get("hours_since_last_episode"), 168.0),  # default: 1 week since episode
    ]
    s = (row.get("stress_event") or "").strip().lower()
    stress = [1.0 if s == (k or "") else 0.0 for k in STRESS_KEYS]
    c = (row.get("context") or "").strip().lower()
    ctx = [1.0 if c == (k or "") else 0.0 for k in CONTEXT_KEYS]
    return np.array(nums + stress + ctx, dtype=np.float64)


def rows_to_matrix(rows: Sequence[dict[str, Any]]) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64)
    return np.vstack([row_to_vector(r) for r in rows])
