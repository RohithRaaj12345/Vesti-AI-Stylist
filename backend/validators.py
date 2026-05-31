"""Input validation for registration (email, mobile, password, name)."""
from __future__ import annotations

import os

import phonenumbers
from email_validator import EmailNotValidError, validate_email

MIN_PASSWORD_LEN = 8
# Default region for parsing local-format mobile numbers (India). Configurable.
PHONE_REGION = os.getenv("PHONE_REGION", "IN")


class ValidationError(ValueError):
    """Raised with a user-friendly message when a field is invalid."""


def clean_name(name: str) -> str:
    name = (name or "").strip()
    if len(name) < 2:
        raise ValidationError("Please enter your name.")
    return name


def clean_email(email: str) -> str:
    try:
        v = validate_email(email or "", check_deliverability=False)
        return v.normalized.lower()
    except EmailNotValidError:
        raise ValidationError("Please enter a valid email address.")


def clean_mobile(mobile: str) -> str:
    """Validate and normalize to E.164 (e.g. +919876543210)."""
    try:
        num = phonenumbers.parse(mobile or "", PHONE_REGION)
    except phonenumbers.NumberParseException:
        raise ValidationError("Please enter a valid mobile number.")
    if not phonenumbers.is_valid_number(num):
        raise ValidationError("Please enter a valid mobile number.")
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)


def clean_password(password: str) -> str:
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    return password
