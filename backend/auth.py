"""Passwords + Redis-backed sessions (token returned to the client, kept in localStorage)."""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException
from passlib.context import CryptContext

from db import SessionLocal, User
from redis_client import r

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
SESSION_TTL = int(os.getenv("SESSION_TTL", str(7 * 24 * 3600)))  # 7 days


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def create_session(user: User) -> str:
    """Make a session token in Redis (`sess:<token>` -> user) and return it."""
    token = secrets.token_urlsafe(32)
    key = f"sess:{token}"
    r.hset(key, mapping={"user_id": user.id, "email": user.email})
    r.expire(key, SESSION_TTL)
    return token


def destroy_session(token: str) -> None:
    if token:
        r.delete(f"sess:{token}")


def token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def current_user(authorization: str | None = Header(default=None)) -> User:
    """FastAPI dependency: resolve the Bearer token via Redis to a User (or 401)."""
    token = token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Please log in.")
    data = r.hgetall(f"sess:{token}")
    if not data:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    with SessionLocal() as s:
        user = s.get(User, data.get("user_id"))
    if user is None:
        raise HTTPException(status_code=401, detail="Account not found. Please log in again.")
    return user
