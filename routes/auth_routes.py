import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash

from models import admin as admin_model
from models import staff as staff_model
from models import user as user_model
from utils.auth import login_user, logout_user, verify_password
from utils.validators import (
    sanitize_input,
    validate_email,
    validate_mobile,
    validate_password_strength,
)

auth_bp = Blueprint("auth", __name__)


def _validate_login_form(identifier, password, require_email=False):
    errors = []
    if not identifier:
        errors.append("Email or username is required." if not require_email else "Email is required.")
    elif require_email and not validate_email(identifier):
        errors.append("Enter a valid email address.")
    if not password:
        errors.append("Password is required.")
    return errors


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = _validate_login_form(email, password, require_email=True)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/login.html", email=email)

        user = user_model.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        if user["status"] != "active":
            flash("Your account is inactive. Contact support.", "warning")
            return render_template("auth/login.html", email=email)

        login_user(user["id"], "citizen", user["full_name"])
        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("citizen.citizen_index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = sanitize_input(request.form.get("name", ""))
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        address = sanitize_input(request.form.get("address", "")) or None

        errors = []
        if not name:
            errors.append("Full name is required.")
        if not mobile:
            errors.append("Mobile number is required.")
        elif not validate_mobile(mobile):
            errors.append("Mobile number must be a valid 10-digit number.")
        if not email:
            errors.append("Email is required.")
        elif not validate_email(email):
            errors.append("Enter a valid email address.")
        if not password:
            errors.append("Password is required.")
        else:
            is_valid_pwd, pwd_err = validate_password_strength(password)
            if not is_valid_pwd:
                errors.append(pwd_err)
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if user_model.get_user_by_email(email):
            errors.append("An account with this email already exists.")
        if user_model.get_user_by_mobile(mobile):
            errors.append("An account with this mobile number already exists.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "auth/register.html",
                name=name,
                mobile=mobile,
                email=email,
                address=address or "",
            )

        user_id = user_model.create_user(name, mobile, email, password, address)
        login_user(user_id, "citizen", name)
        flash("Registration successful. Welcome to QueueLess!", "success")
        return redirect(url_for("citizen.citizen_index"))

    return render_template("auth/register.html")


@auth_bp.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        identifier = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = _validate_login_form(identifier, password)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/staff_login.html", email=identifier)

        staff = staff_model.get_staff_by_identifier(identifier)
        if not staff or not verify_password(password, staff["password_hash"]):
            flash("Invalid staff credentials.", "danger")
            return render_template("auth/staff_login.html", email=identifier)

        if staff["status"] != "active":
            flash("Your staff account is not active.", "warning")
            return render_template("auth/staff_login.html", email=identifier)

        login_user(
            staff["id"],
            "staff",
            staff["name"],
            extra={
                "office_id": staff["office_id"],
                "department_id": staff["department_id"],
                "counter_id": staff["counter_id"],
            },
        )
        flash(f"Welcome, {staff['name']}!", "success")
        return redirect(url_for("staff.staff_index"))

    return render_template("auth/staff_login.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        identifier = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        errors = _validate_login_form(identifier, password)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/admin_login.html", email=identifier)

        admin = admin_model.get_admin_by_identifier(identifier)
        password_ok = False
        if admin:
            try:
                password_ok = check_password_hash(admin["password_hash"], password)
            except (ValueError, TypeError):
                password_ok = False

        if not admin or not password_ok:
            flash("Invalid administrator credentials.", "danger")
            return render_template("auth/admin_login.html", email=identifier)

        if admin["status"] != "active":
            flash("Your administrator account is not active.", "warning")
            return render_template("auth/admin_login.html", email=identifier)

        login_user(admin["id"], "admin", admin["name"])
        flash(f"Welcome, {admin['name']}!", "success")
        return redirect(url_for("admin.admin_index"))

    return render_template("auth/admin_login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))
