"""Shared Redis client for sessions and rate limiting."""
from __future__ import annotations

import os

import redis

# decode_responses=True -> str in/out. Connection is lazy (no connect at import).
r = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)
