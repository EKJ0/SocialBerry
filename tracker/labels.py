from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def hours_between(a: datetime, b: datetime) -> float:
    return (b - a).total_seconds() / 3600.0


def last_episode_before(
    user_id: str, checkin_ts: datetime, episodes: list[dict[str, Any]]
) -> datetime | None:
    same = [parse_ts(e["ts"]) for e in episodes if e["user_id"] == user_id]
    before = [t for t in same if t < checkin_ts]
    return max(before) if before else None


def hours_since_last_episode(
    user_id: str, checkin_ts: datetime, episodes: list[dict[str, Any]]
) -> float | None:
    last = last_episode_before(user_id, checkin_ts, episodes)
    if last is None:
        return None
    return hours_between(last, checkin_ts)


def episode_in_window(
    user_id: str,
    checkin_ts: datetime,
    episodes: list[dict[str, Any]],
    *,
    start_h: float,
    end_h: float,
) -> int:
    """1 if any episode for user in (checkin_ts + start_h, checkin_ts + end_h]."""
    start = checkin_ts + timedelta(hours=start_h)
    end = checkin_ts + timedelta(hours=end_h)
    for e in episodes:
        if e["user_id"] != user_id:
            continue
        t = parse_ts(e["ts"])
        if start < t <= end:
            return 1
    return 0


def enrich_checkin_row(
    row: dict[str, Any],
    episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    uid = row["user_id"]
    ct = parse_ts(row["ts"])
    h = hours_since_last_episode(uid, ct, episodes)
    out = dict(row)
    out["hours_since_last_episode"] = h if h is not None else 9999.0  # no prior episode
    return out


def labels_for_checkin(
    row: dict[str, Any],
    episodes: list[dict[str, Any]],
) -> tuple[int, int]:
    """Binary labels: episode in next 1h, episode in next 24h (exclusive of instant)."""
    uid = row["user_id"]
    ct = parse_ts(row["ts"])
    y1 = episode_in_window(uid, ct, episodes, start_h=0.0, end_h=1.0)
    y24 = episode_in_window(uid, ct, episodes, start_h=0.0, end_h=24.0)
    return y1, y24
