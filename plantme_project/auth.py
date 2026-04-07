from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, TypeVar

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_from_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def make_dev_code() -> str:
    # 6-digit numeric code
    return str(secrets.randbelow(1_000_000)).zfill(6)


def make_serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret_key, salt="plantme-auth-v1")


def issue_token(secret_key: str, payload: dict[str, Any]) -> str:
    s = make_serializer(secret_key)
    return s.dumps(payload)


def verify_token(secret_key: str, token: str, max_age_seconds: int) -> dict[str, Any] | None:
    s = make_serializer(secret_key)
    try:
        obj = s.loads(token, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(obj, dict):
        return None
    return obj


@dataclass(frozen=True)
class AuthedUser:
    user_id: int
    role: str
    identifier: str


F = TypeVar("F", bound=Callable[..., Any])


def parse_bearer(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts
    if scheme.lower() != "bearer":
        return None
    token = token.strip()
    return token or None


def code_expires_at(minutes: int = 10) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def make_invite_code() -> str:
    # short, URL-safe code (no confusing chars)
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(8))

