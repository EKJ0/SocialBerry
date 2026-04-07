from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserCheckIn:
    """Single check-in / signal snapshot for prediction (matches app fields)."""

    anxiety_level: float
    sleep_hours: float | None = None
    caffeine_mg: float | None = None
    heart_rate_bpm: float | None = None
    breathing_rate_bpm: float | None = None
    stress_event: str = ""
    context: str = ""
    food_level: float | None = None
    hours_since_last_episode: float | None = None

    def validate(self) -> None:
        if not 0 <= float(self.anxiety_level) <= 10:
            raise ValueError("anxiety_level must be 0–10")
        if self.sleep_hours is not None and not 0 <= float(self.sleep_hours) <= 24:
            raise ValueError("sleep_hours must be 0–24")
        if self.food_level is not None and not 0 <= float(self.food_level) <= 10:
            raise ValueError("food_level must be 0–10")

    def to_feature_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "anxiety_level": float(self.anxiety_level),
            "sleep_hours": self.sleep_hours,
            "caffeine_mg": self.caffeine_mg,
            "heart_rate_bpm": self.heart_rate_bpm,
            "breathing_rate_bpm": self.breathing_rate_bpm,
            "stress_event": (self.stress_event or "").strip().lower(),
            "context": (self.context or "").strip().lower(),
            "food_level": self.food_level,
            "hours_since_last_episode": self.hours_since_last_episode,
        }


STRESS_KEYS = ("", "conflict", "deadline", "health", "social", "commute", "other")
CONTEXT_KEYS = ("", "home", "work", "commute", "public")


def stress_one_hot(stress: str) -> dict[str, float]:
    s = (stress or "").strip().lower()
    return {f"stress_{k or 'none'}": 1.0 if s == (k or "") else 0.0 for k in STRESS_KEYS}


def context_one_hot(ctx: str) -> dict[str, float]:
    c = (ctx or "").strip().lower()
    return {f"context_{k or 'none'}": 1.0 if c == (k or "") else 0.0 for k in CONTEXT_KEYS}
