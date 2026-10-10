"""Input validation and sanitization utilities for security enforcement."""

import html
import re
from datetime import date, datetime

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
# Indian mobile number format: 10 digits starting with 6, 7, 8, or 9
MOBILE_REGEX = re.compile(r"^[6-9]\d{9}$")


def sanitize_input(text):
    """
    Sanitize user input string against XSS (Cross-Site Scripting) attacks.
    Trims leading/trailing whitespace and escapes dangerous HTML characters.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    # Strip whitespace and escape HTML special characters (<, >, &, ", ')
    return html.escape(text.strip(), quote=True)


def validate_email(email):
    """
    Validate email address format against standard RFC regex.
    Returns True if valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_mobile(mobile):
    """
    Validate 10-digit Indian mobile phone number (starts with 6-9).
    Returns True if valid, False otherwise.
    """
    if not mobile:
        return False
    clean_mobile = str(mobile).strip()
    return bool(MOBILE_REGEX.match(clean_mobile))


def validate_password_strength(password):
    """
    Enforce strong password criteria:
    - Minimum 8 characters in length
    - At least one letter (a-z or A-Z)
    - At least one number (0-9)

    Returns (is_valid: bool, error_message: str).
    """
    if not password or not isinstance(password, str):
        return False, "Password cannot be empty."

    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    return True, ""


def validate_date(date_str, allow_past=False):
    """
    Validate date string format (YYYY-MM-DD).
    If allow_past=False, enforces date >= today (used for appointments & bookings).

    Returns (is_valid: bool, error_message: str).
    """
    if not date_str or not isinstance(date_str, str):
        return False, "Date is required."

    try:
        parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, "Invalid date format. Expected YYYY-MM-DD."

    if not allow_past and parsed_date < date.today():
        return False, "Selected date cannot be in the past."

    return True, ""
