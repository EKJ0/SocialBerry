from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any

def _iso(dt: datetime) -> str:
    return dt.isoformat()


def generate_synthetic_dataset(
    n_users: int = 40,
    checkins_per_user: int = 80,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Rule-based synthetic data: higher anxiety / poor sleep / caffeine / recent episode
    increases chance of a labeled 'episode' in the next 24h (used as training target).
    """
    rng = random.Random(seed)
    checkins: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []

    base = datetime(2025, 1, 1, 8, 0, 0)

    for u in range(n_users):
        user_id = f"syn_user_{u}"
        t = base + timedelta(hours=rng.randint(0, 2000))
        for _ in range(checkins_per_user):
            anxiety = rng.uniform(0, 10)
            sleep = rng.uniform(4.0, 9.0)
            caffeine = rng.uniform(0, 400)
            hr = rng.gauss(75, 12)
            br = rng.gauss(16, 4)
            food = rng.uniform(0, 10)
            stress = rng.choice(["", "deadline", "conflict", "social", "commute"])
            context = rng.choice(["", "home", "work", "commute", "public"])

            checkins.append(
                {
                    "user_id": user_id,
                    "ts": _iso(t),
                    "anxiety_level": round(anxiety, 2),
                    "sleep_hours": round(sleep, 2),
                    "caffeine_mg": round(caffeine, 1),
                    "heart_rate_bpm": max(45.0, min(180.0, round(hr, 1))),
                    "breathing_rate_bpm": max(8.0, min(40.0, round(br, 1))),
                    "stress_event": stress,
                    "context": context,
                    "food_level": round(food, 1),
                }
            )
            t += timedelta(hours=rng.choice([2, 4, 6, 8, 12, 24]))

            # Logistic-style risk for "episode soon" (next check-in window ~ next day)
            z = (
                0.35 * (anxiety - 5)
                + 0.25 * (6.5 - sleep)
                + 0.001 * caffeine
                + 0.02 * (max(0, hr - 75))
                + 0.08 * (max(0, br - 18))
                + 0.15 * (4 - food)
                + (0.4 if stress in {"deadline", "conflict"} else 0)
                + (0.25 if context in {"commute", "public"} else 0)
                - 1.2
            )
            p = 1.0 / (1.0 + math.exp(-z))
            if rng.random() < p * 0.06:
                ep_t = t + timedelta(minutes=rng.randint(20, 55))
                episodes.append({"user_id": user_id, "ts": _iso(ep_t)})
            if rng.random() < p * 0.28:
                ep_t = t + timedelta(minutes=rng.randint(90, 18 * 60))
                episodes.append({"user_id": user_id, "ts": _iso(ep_t)})

    return checkins, episodes
