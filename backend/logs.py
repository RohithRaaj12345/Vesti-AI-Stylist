"""Structured logging: a MySQL `request_logs` row + a rotating server log file.

Also where the dev-mode OTP codes land (logger name "vesti"), under data/app.log.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from db import RequestLog, SessionLocal

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

logger = logging.getLogger("vesti")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    _file = RotatingFileHandler(
        os.path.join(DATA_DIR, "app.log"), maxBytes=5_000_000, backupCount=5
    )
    _file.setFormatter(_fmt)
    logger.addHandler(_file)
    _con = logging.StreamHandler()
    _con.setFormatter(_fmt)
    logger.addHandler(_con)

# Rough INR cost per Gemini call, used for the cost column in the log.
COST_INR = {
    "gemini-2.5-flash-image": 3.7,
    "gemini-3.1-flash-image": 6.4,
    "gemini-3-pro-image": 12.7,
    "gemini-2.5-flash": 0.8,  # analysis (text+vision) — approximate
}


def estimate_cost(model: str | None) -> float:
    return COST_INR.get(model or "", 0.0)


def log_event(
    *,
    action: str,
    status: str,
    user=None,
    ip: str | None = None,
    kind: str | None = None,
    model: str | None = None,
    detail: str | None = None,
    cost_inr: float | None = None,
) -> None:
    """Write one audit row to MySQL and one line to the log file."""
    if cost_inr is None:
        cost_inr = estimate_cost(model)
    email = getattr(user, "email", None)
    try:
        with SessionLocal() as s:
            s.add(
                RequestLog(
                    user_id=getattr(user, "id", None),
                    email=email,
                    ip=ip,
                    action=action,
                    kind=kind,
                    model=model,
                    status=status,
                    detail=(detail or "")[:2000] or None,
                    cost_inr=cost_inr,
                )
            )
            s.commit()
    except Exception as exc:  # never let logging break a request
        logger.warning("request_log write failed: %s", exc)

    logger.info(
        "action=%s status=%s user=%s ip=%s model=%s cost_inr=%.2f detail=%s",
        action, status, email, ip, model, cost_inr, detail,
    )
