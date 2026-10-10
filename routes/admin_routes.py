import csv
import io
import json
import re
from datetime import date
from flask import Blueprint, flash, redirect, render_template, request, url_for, Response, session

from models import admin as admin_model
from models import counter as counter_model
from models import department as department_model
from models import office as office_model
from models import service as service_model
from models import staff as staff_model
from models import user as user_model
from models import appointment as appointment_model
from models import feedback as feedback_model
from utils.auth import admin_required, login_required
from utils.validators import (
    sanitize_input,
    validate_email,
    validate_mobile,
    validate_password_strength,
)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
@admin_required
def admin_index():
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = admin_model.get_admin_dashboard_stats()
    offices = office_model.get_all_offices(status="active")
    chart_data = admin_model.get_all_charts_data()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        offices=offices,
        chart_data=chart_data,
        chart_data_json=json.dumps(chart_data)
    )


@admin_bp.route("/register", methods=["GET", "POST"])
def register_admin():
    """Register a new administrator with credentials and role security."""
    is_admin_session = session.get("logged_in") and session.get("role") == "admin"

    if request.method == "POST":
        name = sanitize_input(request.form.get("full_name") or request.form.get("name") or "").strip()
        username = sanitize_input(request.form.get("username", "")).strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Administrator Full Name is required.")

        if not username:
            errors.append("Admin username is required.")
        elif not re.match(r"^[a-zA-Z0-9_.-]{3,30}$", username):
            errors.append("Username must be between 3 and 30 characters (letters, numbers, underscore, hyphen, dot).")
        elif admin_model.get_admin_by_username(username):
            errors.append(f"The username '{username}' is already in use by another admin.")

        if not email:
            errors.append("Email address is required.")
        elif not validate_email(email):
            errors.append("Please enter a valid email address.")
        elif admin_model.get_admin_by_email(email):
            errors.append(f"An admin account with email '{email}' already exists.")

        if not password:
            errors.append("Password is required.")
        else:
            is_valid_pwd, pwd_err = validate_password_strength(password)
            if not is_valid_pwd:
                errors.append(pwd_err)

        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            if is_admin_session:
                admins_list = admin_model.get_all_admins()
                return render_template(
                    "admin/register_admin.html",
                    name=name,
                    username=username,
                    email=email,
                    admins=admins_list,
                )
            return render_template(
                "register_admin.html",
                full_name=name,
                name=name,
                username=username,
                email=email,
            )

        try:
            admin_model.create_admin(
                name=name,
                email=email,
                raw_password=password,
                username=username,
                status="active",
            )
            flash(f"Administrator account for '{name}' (@{username}) successfully created! Please log in to continue.", "success")
            if is_admin_session:
                return redirect(url_for("admin.register_admin"))
            return redirect(url_for("admin_login"))
        except Exception as exc:
            flash(f"Failed to create admin account: {exc}", "danger")

    if is_admin_session:
        admins_list = admin_model.get_all_admins()
        return render_template("admin/register_admin.html", admins=admins_list)
    return render_template("register_admin.html")


@admin_bp.route("/offices", methods=["GET", "POST"])
@login_required
@admin_required
def offices():
    if request.method == "POST":
        action = request.form.get("action", "add")

        if action == "toggle":
            office_id = request.form.get("office_id")
            if office_id:
                office_model.toggle_office_status(int(office_id))
                flash("Office status updated.", "success")
            return redirect(url_for("admin.offices"))

        if action == "update":
            try:
                office_model.update_office(
                    int(request.form.get("office_id")),
                    request.form.get("office_name", "").strip(),
                    request.form.get("address", "").strip(),
                    request.form.get("city", "").strip(),
                    request.form.get("phone", "").strip(),
                    request.form.get("opening_time"),
                    request.form.get("closing_time"),
                    request.form.get("status", "active"),
                )
                flash("Office updated successfully.", "success")
            except Exception:
                flash("Failed to update office.", "danger")
            return redirect(url_for("admin.offices"))

        office_name = request.form.get("office_name", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()

        if not office_name or not address or not city:
            flash("Office name, address, and city are required.", "danger")
        else:
            try:
                office_model.add_office(
                    office_name,
                    address,
                    city,
                    request.form.get("phone", "").strip(),
                    request.form.get("opening_time", "09:00"),
                    request.form.get("closing_time", "17:00"),
                    request.form.get("status", "active"),
                )
                flash("Office added successfully.", "success")
            except Exception:
                flash("Failed to add office.", "danger")

        return redirect(url_for("admin.offices"))

    all_offices = office_model.get_all_offices()
    return render_template("admin/offices.html", offices=all_offices)


@admin_bp.route("/departments", methods=["GET", "POST"])
@login_required
@admin_required
def departments():
    office_id = request.args.get("office_id", type=int)
    all_offices = office_model.get_all_offices()

    if request.method == "POST":
        action = request.form.get("action", "add")
        office_id = request.form.get("office_id", type=int) or office_id

        if action == "toggle":
            dept_id = request.form.get("department_id")
            if dept_id:
                department_model.toggle_department_status(int(dept_id))
                flash("Department status updated.", "success")
            return redirect(url_for("admin.departments", office_id=office_id))

        if action == "update":
            try:
                department_model.update_department(
                    int(request.form.get("department_id")),
                    int(request.form.get("office_id")),
                    request.form.get("department_name", "").strip(),
                    request.form.get("description", "").strip() or None,
                    request.form.get("status", "active"),
                )
                flash("Department updated successfully.", "success")
            except Exception:
                flash("Failed to update department.", "danger")
            return redirect(url_for("admin.departments", office_id=office_id))

        dept_name = request.form.get("department_name", "").strip()
        if not office_id or not dept_name:
            flash("Office and department name are required.", "danger")
        else:
            try:
                department_model.add_department(
                    office_id,
                    dept_name,
                    request.form.get("description", "").strip() or None,
                    request.form.get("status", "active"),
                )
                flash("Department added successfully.", "success")
            except Exception:
                flash("Failed to add department.", "danger")

        return redirect(url_for("admin.departments", office_id=office_id))

    if office_id:
        dept_list = department_model.get_departments_by_office(office_id)
    else:
        dept_list = department_model.get_all_departments()

    return render_template(
        "admin/departments.html",
        departments=dept_list,
        offices=all_offices,
        selected_office_id=office_id,
    )


@admin_bp.route("/services", methods=["GET", "POST"])
@login_required
@admin_required
def services():
    department_id = request.args.get("department_id", type=int)
    all_departments = department_model.get_all_departments()

    if request.method == "POST":
        action = request.form.get("action", "add")
        department_id = request.form.get("department_id", type=int) or department_id

        if action == "toggle":
            service_id = request.form.get("service_id")
            if service_id:
                service_model.toggle_service_status(int(service_id))
                flash("Service status updated.", "success")
            return redirect(url_for("admin.services", department_id=department_id))

        if action == "update":
            try:
                service_model.update_service(
                    int(request.form.get("service_id")),
                    int(request.form.get("department_id")),
                    request.form.get("service_name", "").strip(),
                    request.form.get("description", "").strip() or None,
                    int(request.form.get("average_time", 15)),
                    int(request.form.get("daily_limit", 100)),
                    request.form.get("status", "active"),
                )
                flash("Service updated successfully.", "success")
            except Exception:
                flash("Failed to update service.", "danger")
            return redirect(url_for("admin.services", department_id=department_id))

        service_name = request.form.get("service_name", "").strip()
        if not department_id or not service_name:
            flash("Department and service name are required.", "danger")
        else:
            try:
                service_model.add_service(
                    department_id,
                    service_name,
                    request.form.get("description", "").strip() or None,
                    int(request.form.get("average_time", 15)),
                    int(request.form.get("daily_limit", 100)),
                    request.form.get("status", "active"),
                )
                flash("Service added successfully.", "success")
            except Exception:
                flash("Failed to add service.", "danger")

        return redirect(url_for("admin.services", department_id=department_id))

    if department_id:
        service_list = service_model.get_services_by_department(department_id)
    else:
        service_list = service_model.get_all_services()

    return render_template(
        "admin/services.html",
        services=service_list,
        departments=all_departments,
        selected_department_id=department_id,
    )


@admin_bp.route("/counters", methods=["GET", "POST"])
@login_required
@admin_required
def counters():
    office_id = request.args.get("office_id", type=int)
    all_offices = office_model.get_all_offices()
    all_departments = department_model.get_all_departments()

    if request.method == "POST":
        action = request.form.get("action", "add")
        office_id = request.form.get("office_id", type=int) or office_id

        if action == "toggle":
            counter_id = request.form.get("counter_id")
            if counter_id:
                counter_model.toggle_counter_status(int(counter_id))
                flash("Counter status updated.", "success")
            return redirect(url_for("admin.counters", office_id=office_id))

        if action == "update":
            try:
                counter_model.update_counter(
                    int(request.form.get("counter_id")),
                    int(request.form.get("office_id")),
                    int(request.form.get("department_id")),
                    request.form.get("counter_number", "").strip(),
                    request.form.get("status", "active"),
                )
                flash("Counter updated successfully.", "success")
            except Exception:
                flash("Failed to update counter.", "danger")
            return redirect(url_for("admin.counters", office_id=office_id))

        counter_number = request.form.get("counter_number", "").strip()
        dept_id = request.form.get("department_id", type=int)
        if not office_id or not dept_id or not counter_number:
            flash("Office, department, and counter number are required.", "danger")
        else:
            try:
                counter_model.add_counter(office_id, dept_id, counter_number)
                flash("Counter added successfully.", "success")
            except Exception:
                flash("Failed to add counter. It may already exist.", "danger")

        return redirect(url_for("admin.counters", office_id=office_id))

    if office_id:
        counter_list = counter_model.get_counters_by_office(office_id)
    else:
        counter_list = counter_model.get_all_counters()

    return render_template(
        "admin/counters.html",
        counters=counter_list,
        offices=all_offices,
        departments=all_departments,
        selected_office_id=office_id,
    )


@admin_bp.route("/staff", methods=["GET", "POST"])
@login_required
@admin_required
def staff():
    all_offices = office_model.get_all_offices()
    all_departments = department_model.get_all_departments()
    all_counters = counter_model.get_all_counters()

    if request.method == "POST":
        action = request.form.get("action", "add")

        if action == "toggle":
            staff_id = request.form.get("staff_id")
            if staff_id:
                staff_model.toggle_staff_status(int(staff_id))
                flash("Staff status updated.", "success")
            return redirect(url_for("admin.staff"))

        if action == "update":
            counter_id = request.form.get("counter_id") or None
            if counter_id:
                counter_id = int(counter_id)
            raw_password = request.form.get("password", "").strip() or None
            try:
                staff_model.update_staff(
                    int(request.form.get("staff_id")),
                    int(request.form.get("office_id")),
                    int(request.form.get("department_id")),
                    request.form.get("name", "").strip(),
                    request.form.get("mobile", "").strip(),
                    request.form.get("email", "").strip().lower(),
                    counter_id,
                    request.form.get("status", "active"),
                    raw_password=raw_password,
                )
                flash("Staff member updated successfully.", "success")
            except Exception:
                flash("Failed to update staff member.", "danger")
            return redirect(url_for("admin.staff"))

        name = sanitize_input(request.form.get("name", ""))
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "").strip()
        office_id = request.form.get("office_id", type=int)
        dept_id = request.form.get("department_id", type=int)
        counter_id = request.form.get("counter_id") or None

        username = sanitize_input(request.form.get("username", "")).strip().lower() or email.split("@")[0]
        if not all([name, email, mobile, password, office_id, dept_id]):
            flash("Name, email, mobile, password, office, and department are required.", "danger")
        elif not validate_email(email):
            flash("Please enter a valid email address.", "danger")
        elif not validate_mobile(mobile):
            flash("Please enter a valid 10-digit mobile number.", "danger")
        elif staff_model.get_staff_by_email(email):
            flash("A staff member with this email already exists.", "danger")
        else:
            is_valid_pwd, pwd_err = validate_password_strength(password)
            if not is_valid_pwd:
                flash(pwd_err, "danger")
            else:
                try:
                    staff_model.add_staff(
                        office_id,
                        dept_id,
                        name,
                        mobile,
                        email,
                        password,
                        int(counter_id) if counter_id else None,
                        status="active",
                        username=username,
                    )
                    flash("Staff member added successfully.", "success")
                except Exception:
                    flash("Failed to add staff member.", "danger")

        return redirect(url_for("admin.staff"))

    staff_list = staff_model.get_all_staff()
    return render_template(
        "admin/staff.html",
        staff_list=staff_list,
        offices=all_offices,
        departments=all_departments,
        counters=all_counters,
    )


@admin_bp.route("/add-staff", methods=["GET", "POST"])
@login_required
@admin_required
def add_staff_page():
    """Dedicated registration portal for new Staff members with counter and department assignments."""
    all_offices = office_model.get_all_offices(status="active")
    all_departments = department_model.get_all_departments(status="active")
    all_counters = counter_model.get_all_counters(status="active")

    if request.method == "POST":
        name = sanitize_input(request.form.get("name", "")).strip()
        username = sanitize_input(request.form.get("username", "")).strip().lower()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        office_id = request.form.get("office_id", type=int)
        dept_id = request.form.get("department_id", type=int)
        counter_id = request.form.get("counter_id") or None
        if counter_id:
            try:
                counter_id = int(counter_id)
            except ValueError:
                counter_id = None

        errors = []
        if not name:
            errors.append("Staff Full Name is required.")

        if not username:
            errors.append("Staff username is required.")
        elif not re.match(r"^[a-zA-Z0-9_.-]{3,30}$", username):
            errors.append("Username must be between 3 and 30 characters (letters, numbers, underscore, hyphen, dot).")
        elif staff_model.get_staff_by_username(username):
            errors.append(f"A staff member with username '{username}' already exists.")

        if not email:
            errors.append("Email address is required.")
        elif not validate_email(email):
            errors.append("Please provide a valid email address.")
        elif staff_model.get_staff_by_email(email):
            errors.append(f"A staff member with email '{email}' already exists.")

        if not mobile:
            errors.append("Mobile number is required.")
        elif not validate_mobile(mobile):
            errors.append("Please provide a valid 10-digit mobile number.")
        elif staff_model.get_staff_by_mobile(mobile):
            errors.append(f"A staff member with mobile number '{mobile}' already exists.")

        if not office_id:
            errors.append("Please select an assigned Government Office.")
        if not dept_id:
            errors.append("Please select an assigned Department.")

        if not password:
            errors.append("Password is required.")
        else:
            is_valid_pwd, pwd_err = validate_password_strength(password)
            if not is_valid_pwd:
                errors.append(pwd_err)

        if password and confirm_password and password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "admin/register_staff.html",
                name=name,
                username=username,
                email=email,
                mobile=mobile,
                selected_office_id=office_id,
                selected_dept_id=dept_id,
                selected_counter_id=counter_id,
                offices=all_offices,
                departments=all_departments,
                counters=all_counters,
            )

        try:
            staff_model.add_staff(
                office_id=office_id,
                department_id=dept_id,
                name=name,
                mobile=mobile,
                email=email,
                raw_password=password,
                counter_id=counter_id,
                status="active",
                username=username,
            )
            flash(f"Staff member '{name}' (@{username}) successfully registered and assigned!", "success")
            return redirect(url_for("admin.staff"))
        except Exception as exc:
            flash(f"Failed to register staff: {exc}", "danger")

    return render_template(
        "admin/register_staff.html",
        offices=all_offices,
        departments=all_departments,
        counters=all_counters,
    )


@admin_bp.route("/citizens", methods=["GET", "POST"])
@login_required
@admin_required
def citizens():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id:
            user_model.toggle_citizen_status(int(user_id))
            flash("Citizen status updated.", "success")
        return redirect(url_for("admin.citizens"))

    citizens_list = user_model.get_all_citizens()
    return render_template("admin/citizens.html", citizens=citizens_list)


@admin_bp.route("/appointments")
@login_required
@admin_required
def appointments():
    appointments_list = appointment_model.get_all_appointments_admin()
    return render_template("admin/appointments.html", appointments=appointments_list)


@admin_bp.route("/feedback")
@login_required
@admin_required
def feedback():
    office_id = request.args.get("office_id", type=int)
    service_id = request.args.get("service_id", type=int)
    rating = request.args.get("rating", type=int)

    feedback_list = feedback_model.get_all_feedback_admin(
        office_id=office_id,
        service_id=service_id,
        rating=rating
    )
    service_summary = feedback_model.get_service_rating_summary()
    overall_stats = feedback_model.get_overall_feedback_stats()
    all_offices = office_model.get_all_offices()
    all_services = service_model.get_all_services()

    return render_template(
        "admin/feedback.html",
        feedback_list=feedback_list,
        service_summary=service_summary,
        overall_stats=overall_stats,
        offices=all_offices,
        services=all_services,
        selected_office=office_id,
        selected_service=service_id,
        selected_rating=rating,
    )


@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    office_id = request.args.get("office_id", type=int)
    department_id = request.args.get("department_id", type=int)
    service_id = request.args.get("service_id", type=int)
    status = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    reports_data = admin_model.get_filtered_reports(
        office_id=office_id,
        department_id=department_id,
        service_id=service_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    all_offices = office_model.get_all_offices()
    all_departments = department_model.get_all_departments()
    all_services = service_model.get_all_services()

    return render_template(
        "admin/reports.html",
        reports=reports_data,
        offices=all_offices,
        departments=all_departments,
        services=all_services,
        selected_office=office_id,
        selected_department=department_id,
        selected_service=service_id,
        selected_status=status,
        selected_start_date=start_date,
        selected_end_date=end_date,
    )


@admin_bp.route("/reports/export")
@login_required
@admin_required
def export_reports_csv():
    office_id = request.args.get("office_id", type=int)
    department_id = request.args.get("department_id", type=int)
    service_id = request.args.get("service_id", type=int)
    status = request.args.get("status")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    reports_data = admin_model.get_filtered_reports(
        office_id=office_id,
        department_id=department_id,
        service_id=service_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Token ID",
        "Token Number",
        "Date",
        "Status",
        "Citizen Name",
        "Citizen Mobile",
        "Office",
        "Department",
        "Service",
        "Counter",
        "Created At",
        "Called At",
        "Completed At"
    ])

    for row in reports_data:
        writer.writerow([
            row.get("id"),
            row.get("token_number"),
            row.get("token_date"),
            (row.get("status") or "").upper(),
            row.get("citizen_name"),
            row.get("citizen_mobile"),
            row.get("office_name"),
            row.get("department_name"),
            row.get("service_name"),
            row.get("counter_number"),
            row.get("created_at"),
            row.get("called_at") or "—",
            row.get("completed_at") or "—"
        ])

    csv_content = output.getvalue()
    filename = f"QueueLess_Token_Report_{date.today().strftime('%Y%m%d')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

