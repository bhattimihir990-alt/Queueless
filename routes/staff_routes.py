from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import staff as staff_model
from models import token as token_model
from models import appointment as appointment_model
from utils.auth import login_required, session, staff_required

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/")
@staff_bp.route("/dashboard")
@login_required
@staff_required
def staff_index():
    staff_id = session.get("user_id")
    staff_info = staff_model.get_staff_assignment_details(staff_id)

    if not staff_info:
        flash("Staff profile details not found.", "danger")
        return redirect(url_for("home"))

    counter_id = staff_info.get("counter_id")
    office_id = staff_info.get("office_id")
    dept_id = staff_info.get("department_id")

    current_token = (
        token_model.get_current_counter_token(counter_id) if counter_id else None
    )
    waiting_queue = (
        token_model.get_staff_counter_queue(office_id, dept_id)
        if (office_id and dept_id)
        else []
    )
    next_token = waiting_queue[0] if waiting_queue else None
    history = token_model.get_staff_history(counter_id) if counter_id else []

    return render_template(
        "staff/dashboard.html",
        staff_info=staff_info,
        current_token=current_token,
        next_token=next_token,
        waiting_queue=waiting_queue,
        history=history,
    )


@staff_bp.route("/token/next", methods=["POST"])
@login_required
@staff_required
def call_next():
    staff_id = session.get("user_id")
    staff_info = staff_model.get_staff_assignment_details(staff_id)

    if not staff_info or not staff_info.get("counter_id"):
        flash("No counter assigned to your staff account.", "warning")
        return redirect(url_for("staff.staff_index"))

    token = token_model.call_next_token(
        staff_id=staff_id,
        counter_id=staff_info["counter_id"],
        office_id=staff_info["office_id"],
        department_id=staff_info["department_id"],
    )

    if token:
        flash(f"Token {token['token_number']} CALLED.", "success")
    else:
        flash("No waiting tokens in queue.", "info")

    return redirect(url_for("staff.staff_index"))


def _verify_staff_token_access(token_id, staff_id):
    """Ensure staff can only operate on tokens within their assigned office and department."""
    staff_info = staff_model.get_staff_assignment_details(staff_id)
    if not staff_info:
        return False, None
    token = token_model.get_token_by_id(token_id)
    if not token:
        return False, None
    if token["office_id"] != staff_info["office_id"] or token["department_id"] != staff_info["department_id"]:
        return False, None
    return True, token


@staff_bp.route("/token/serve", methods=["POST"])
@login_required
@staff_required
def serve_token():
    token_id = request.form.get("token_id", type=int)
    staff_id = session.get("user_id")
    if token_id:
        allowed, token = _verify_staff_token_access(token_id, staff_id)
        if not allowed:
            flash("Access denied: You cannot process tokens outside your assigned department.", "danger")
            return redirect(url_for("staff.staff_index"))
        token = token_model.start_serving_token(token_id)
        if token:
            flash(f"Serving Token {token['token_number']}.", "success")
    return redirect(url_for("staff.staff_index"))


@staff_bp.route("/token/complete", methods=["POST"])
@login_required
@staff_required
def complete_token():
    token_id = request.form.get("token_id", type=int)
    staff_id = session.get("user_id")
    if token_id:
        allowed, token = _verify_staff_token_access(token_id, staff_id)
        if not allowed:
            flash("Access denied: You cannot process tokens outside your assigned department.", "danger")
            return redirect(url_for("staff.staff_index"))
        token = token_model.complete_token(token_id)
        if token:
            flash(f"Token {token['token_number']} COMPLETED.", "success")
    return redirect(url_for("staff.staff_index"))


@staff_bp.route("/token/skip", methods=["POST"])
@login_required
@staff_required
def skip_token():
    token_id = request.form.get("token_id", type=int)
    staff_id = session.get("user_id")
    if token_id:
        allowed, token = _verify_staff_token_access(token_id, staff_id)
        if not allowed:
            flash("Access denied: You cannot process tokens outside your assigned department.", "danger")
            return redirect(url_for("staff.staff_index"))
        token = token_model.skip_token(token_id)
        if token:
            flash(f"Token {token['token_number']} SKIPPED (No-Show).", "warning")
    return redirect(url_for("staff.staff_index"))


@staff_bp.route("/token/recall", methods=["POST"])
@login_required
@staff_required
def recall_token():
    token_id = request.form.get("token_id", type=int)
    staff_id = session.get("user_id")
    if token_id:
        allowed, token = _verify_staff_token_access(token_id, staff_id)
        if not allowed:
            flash("Access denied: You cannot process tokens outside your assigned department.", "danger")
            return redirect(url_for("staff.staff_index"))
        token = token_model.recall_token(token_id)
        if token:
            flash(f"Token {token['token_number']} RECALLED.", "info")
    return redirect(url_for("staff.staff_index"))


@staff_bp.route("/queue")
@login_required
@staff_required
def queue():
    staff_id = session.get("user_id")
    staff_info = staff_model.get_staff_assignment_details(staff_id)

    if not staff_info:
        flash("Staff profile details not found.", "danger")
        return redirect(url_for("home"))

    counter_id = staff_info.get("counter_id")
    office_id = staff_info.get("office_id")
    dept_id = staff_info.get("department_id")

    waiting_queue = (
        token_model.get_staff_counter_queue(office_id, dept_id)
        if (office_id and dept_id)
        else []
    )
    history = token_model.get_staff_history(counter_id) if counter_id else []

    return render_template(
        "staff/queue.html",
        staff_info=staff_info,
        waiting_queue=waiting_queue,
        history=history,
    )


@staff_bp.route("/appointments")
@login_required
@staff_required
def appointments():
    staff_id = session.get("user_id")
    staff_info = staff_model.get_staff_assignment_details(staff_id)

    if not staff_info:
        flash("Staff profile details not found.", "danger")
        return redirect(url_for("home"))
        
    office_id = staff_info.get("office_id")
    dept_id = staff_info.get("department_id")
    
    appointments_list = appointment_model.get_todays_appointments_staff(office_id, dept_id) if office_id and dept_id else []
    
    return render_template(
        "staff/appointments.html", 
        appointments=appointments_list, 
        staff_info=staff_info
    )
