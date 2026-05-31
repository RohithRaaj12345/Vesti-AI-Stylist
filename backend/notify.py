"""Email OTP delivery via SMTP.

If SMTP is configured (SMTP_HOST set), codes are emailed for real. Otherwise, in
dev mode, the code is just written to the log so the flow still works locally.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("vesti")

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "no-reply@vesti.app")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}

# Fallback when SMTP isn't configured: just log the code (dev only).
DEV_MODE = os.getenv("OTP_DEV_MODE", "true").lower() in {"1", "true", "yes"}


def smtp_enabled() -> bool:
    """Real SMTP send only when both host and a username are configured."""
    return bool(SMTP_HOST and SMTP_USERNAME)


def send_email_otp(email: str, code: str) -> None:
    if smtp_enabled():
        msg = EmailMessage()
        msg["Subject"] = "Your Vesti verification code"
        msg["From"] = SMTP_FROM
        msg["To"] = email
        msg.set_content(
            f"Your Vesti verification code is: {code}\n\n"
            "It expires in 10 minutes. If you didn't request this, you can ignore this email."
        )
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            if SMTP_STARTTLS:
                s.starttls(context=ssl.create_default_context())
            if SMTP_USERNAME:
                s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        log.info("Sent OTP email to %s via SMTP", email)
        return

    if DEV_MODE:
        log.info("[DEV OTP] email to %s -> code %s", email, code)
        return

    raise RuntimeError("Email OTP is not configured (set SMTP_HOST, or OTP_DEV_MODE=true).")
