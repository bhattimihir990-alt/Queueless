"""Authentication helpers, session management, and role-based decorators."""

from functools import wraps

import bcrypt
from flask import abort, flash, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(raw_password):
    """Hash a plain-text password using Werkzeug (compatible with check_password_hash)."""
    return generate_password_hash(raw_password)


def verify_password(raw_password, password_hash):
    """Verify a plain-text password against a stored hash."""
    if not password_hash:
        return False

    try:
        if check_password_hash(password_hash, raw_password):
            return True
    except (ValueError, TypeError):
        pass

    if password_hash.startswith("$2"):
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    return False


def login_user(user_id, role, name, extra=None):
    """Store authenticated user details in the session."""
    session.clear()
    session["user_id"] = user_id
    session["role"] = role
    session["name"] = name
    session["logged_in"] = True

    if extra:
        for key, value in extra.items():
            session[key] = value

    session.modified = True


def logout_user():
    """Clear the current user session."""
    session.clear()


def get_current_user():
    """Return a dict of the current session user, or None if not logged in."""
    if not session.get("logged_in"):
        return None

    return {
        "user_id": session.get("user_id"),
        "role": session.get("role"),
        "name": session.get("name"),
    }


def is_logged_in():
    return session.get("logged_in") is True


def has_role(role):
    return is_logged_in() and session.get("role") == role


def login_required(view_func):
    """Require any authenticated user."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper


def citizen_required(view_func):
    """Require an authenticated citizen."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in as a citizen to continue.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "citizen":
            abort(403)
        return view_func(*args, **kwargs)

    return wrapper


def staff_required(view_func):
    """Require an authenticated staff member."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in as staff to continue.", "warning")
            return redirect(url_for("auth.staff_login"))
        if session.get("role") != "staff":
            abort(403)
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Require an authenticated administrator."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in as an administrator to continue.", "warning")
            return redirect(url_for("auth.admin_login"))
        if session.get("role") != "admin":
            abort(403)
        return view_func(*args, **kwargs)

    return wrapper
