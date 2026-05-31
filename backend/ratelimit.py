"""Per-user upload rate limiting via a Redis key with a TTL.

Quota is consumed only when an upload actually succeeds (we `mark` after the work),
so failed/invalid uploads don't lock the user out.
"""
from __future__ import annotations

import os

from redis_client import r

WINDOW_MIN = int(os.getenv("RATE_LIMIT_WINDOW_MIN", "5"))


def _key(user_id: str) -> str:
    return f"upload:{user_id}"


def seconds_until_allowed(user_id: str) -> int:
    """0 if the user may upload now, else seconds remaining in the window."""
    ttl = r.ttl(_key(user_id))
    return ttl if ttl and ttl > 0 else 0


def mark(user_id: str) -> None:
    """Record a successful upload; blocks further uploads for the window."""
    r.set(_key(user_id), "1", ex=WINDOW_MIN * 60)
