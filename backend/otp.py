"""Issue and verify 6-digit OTP codes, persisted in the MySQL `otps` table."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

import notify
from db import Otp, User

OTP_TTL_MIN = 10
MAX_ATTEMPTS = 5


class OtpError(ValueError):
    """User-friendly OTP failure."""


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def issue_otp(session, user: User, channel: str) -> str:
    """Create + store a code, deliver it, and return the plaintext (dev use)."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    session.add(
        Otp(
            user_id=user.id,
            channel=channel,
            code_hash=_hash(code),
            expires_at=datetime.utcnow() + timedelta(minutes=OTP_TTL_MIN),
        )
    )
    session.commit()
    # Only email OTP is supported (phone verification was removed).
    notify.send_email_otp(user.email, code)
    return code


def verify_otp(session, user: User, channel: str, code: str) -> None:
    """Validate the latest code for user+channel; mark the user verified on success."""
    otp = (
        session.query(Otp)
        .filter(Otp.user_id == user.id, Otp.channel == channel, Otp.consumed.is_(False))
        .order_by(Otp.created_at.desc())
        .first()
    )
    if otp is None:
        raise OtpError("No code found. Please request a new code.")
    if otp.expires_at < datetime.utcnow():
        raise OtpError("This code has expired. Please request a new one.")
    if otp.attempts >= MAX_ATTEMPTS:
        raise OtpError("Too many attempts. Please request a new code.")
    if otp.code_hash != _hash((code or "").strip()):
        otp.attempts += 1
        session.commit()
        raise OtpError("Incorrect code.")

    otp.consumed = True
    if channel == "email":
        user.email_verified = True
    else:
        user.phone_verified = True
    session.commit()
