from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import department as department_model
from models import office as office_model
from models import service as service_model
from models import token as token_model
from models import appointment as appointment_model
from models import feedback as feedback_model
from utils.auth import citizen_required, login_required, session
from utils.validators import sanitize_input, validate_date

citizen_bp = Blueprint("citizen", __name__)


@citizen_bp.route("/")
@citizen_bp.route("/dashboard")
@login_required
@citizen_required
def citizen_index():
    user_id = session.get("user_id")
    active_token = token_model.get_active_user_token(user_id)
    queue_status = (
        token_model.get_queue_status_for_token(active_token["id"])
        if active_token
        else None
    )
    history = token_model.get_user_token_history(user_id, limit=5)
    return render_template(
        "citizen/dashboard.html",
        active_token=active_token,
        queue_status=queue_status,
        history=history,
    )


@citizen_bp.route("/offices")
@login_required
@citizen_required
def offices():
    all_offices = office_model.get_all_offices(status="active")
    return render_template("citizen/offices.html", offices=all_offices)


@citizen_bp.route("/office/<int:office_id>")
@login_required
@citizen_required
def office_detail(office_id):
    office = office_model.get_office_hierarchy(office_id)
    if not office:
        flash("Office not found or inactive.", "warning")
        return redirect(url_for("citizen.offices"))
    return render_template("citizen/office_detail.html", office=office)


@citizen_bp.route("/token/generate", methods=["GET", "POST"])
@login_required
@citizen_required
def generate_token():
    user_id = session.get("user_id")

    if request.method == "POST":
        office_id = request.form.get("office_id", type=int)
        dept_id = request.form.get("department_id", type=int)
        service_id = request.form.get("service_id", type=int)

        if not office_id or not dept_id or not service_id:
            flash("Please select an office, department, and service.", "danger")
            return redirect(url_for("citizen.generate_token"))

        try:
            token_info = token_model.generate_token(
                user_id=user_id,
                office_id=office_id,
                department_id=dept_id,
                service_id=service_id,
            )
            flash(
                f"Token {token_info['token_number']} generated successfully!",
                "success",
            )
            return redirect(
                url_for("citizen.token_detail", token_id=token_info["id"])
            )
        except ValueError as err:
            flash(str(err), "warning")
            return redirect(url_for("citizen.citizen_index"))
        except Exception as exc:
            flash(f"Failed to generate token: {exc}", "danger")
            return redirect(url_for("citizen.generate_token"))

    selected_office_id = request.args.get("office_id", type=int)
    selected_dept_id = request.args.get("department_id", type=int)
    selected_service_id = request.args.get("service_id", type=int)

    all_offices = office_model.get_all_offices(status="active")
    all_departments = department_model.get_all_departments(status="active")
    all_services = service_model.get_all_services(status="active")

    return render_template(
        "citizen/generate_token.html",
        offices=all_offices,
        departments=all_departments,
        services=all_services,
        selected_office_id=selected_office_id,
        selected_dept_id=selected_dept_id,
        selected_service_id=selected_service_id,
    )


@citizen_bp.route("/token/<int:token_id>")
@login_required
@citizen_required
def token_detail(token_id):
    user_id = session.get("user_id")
    token = token_model.get_token_by_id(token_id)

    if not token or token["user_id"] != user_id:
        flash("Token not found.", "warning")
        return redirect(url_for("citizen.citizen_index"))

    queue_status = token_model.get_queue_status_for_token(token_id)
    return render_template(
        "citizen/token_detail.html",
        token=token,
        queue_status=queue_status,
    )


@citizen_bp.route("/queue/<int:token_id>")
@login_required
@citizen_required
def live_queue(token_id):
    user_id = session.get("user_id")
    token = token_model.get_token_by_id(token_id)

    if not token or token["user_id"] != user_id:
        flash("Token not found.", "warning")
        return redirect(url_for("citizen.citizen_index"))

    queue_status = token_model.get_queue_status_for_token(token_id)
    return render_template(
        "citizen/live_queue.html",
        token=token,
        queue_status=queue_status,
    )


@citizen_bp.route("/token/cancel", methods=["POST"])
@login_required
@citizen_required
def cancel_token():
    user_id = session.get("user_id")
    token_id = request.form.get("token_id", type=int)

    if token_id:
        token_model.cancel_token(token_id, user_id)
        flash("Token cancelled successfully.", "info")

    return redirect(url_for("citizen.citizen_index"))


@citizen_bp.route("/history")
@login_required
@citizen_required
def history():
    user_id = session.get("user_id")
    history_list = token_model.get_user_token_history(user_id, limit=50)
    return render_template("citizen/history.html", history=history_list)


@citizen_bp.route("/appointments/book", methods=["GET", "POST"])
@login_required
@citizen_required
def book_appointment():
    user_id = session.get("user_id")

    if request.method == "POST":
        office_id = request.form.get("office_id", type=int)
        dept_id = request.form.get("department_id", type=int)
        service_id = request.form.get("service_id", type=int)
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")

        if not all([office_id, dept_id, service_id, appointment_date, appointment_time]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("citizen.book_appointment"))

        is_valid_date, date_err = validate_date(appointment_date, allow_past=False)
        if not is_valid_date:
            flash(date_err, "danger")
            return redirect(url_for("citizen.book_appointment"))

        success, message = appointment_model.create_appointment(
            user_id=user_id,
            office_id=office_id,
            department_id=dept_id,
            service_id=service_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )
        if success:
            flash(message, "success")
            return redirect(url_for("citizen.my_appointments"))
        else:
            flash(message, "warning")
            return redirect(url_for("citizen.book_appointment"))

    all_offices = office_model.get_all_offices(status="active")
    all_departments = department_model.get_all_departments(status="active")
    all_services = service_model.get_all_services(status="active")

    return render_template(
        "citizen/book_appointment.html",
        offices=all_offices,
        departments=all_departments,
        services=all_services
    )


@citizen_bp.route("/appointments")
@login_required
@citizen_required
def my_appointments():
    user_id = session.get("user_id")
    appointments = appointment_model.get_user_appointments(user_id)
    return render_template("citizen/my_appointments.html", appointments=appointments)


@citizen_bp.route("/appointments/cancel", methods=["POST"])
@login_required
@citizen_required
def cancel_appointment():
    user_id = session.get("user_id")
    appointment_id = request.form.get("appointment_id", type=int)

    if appointment_id:
        appointment_model.cancel_appointment(appointment_id, user_id)
        flash("Appointment cancelled successfully.", "info")

    return redirect(url_for("citizen.my_appointments"))


@citizen_bp.route("/notifications")
@login_required
@citizen_required
def notifications():
    user_id = session.get("user_id")
    from models import notifications as notif_model
    notifs = notif_model.get_user_notifications(user_id)
    return render_template("citizen/notifications.html", notifications=notifs)


@citizen_bp.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
@login_required
@citizen_required
def mark_read(notification_id):
    user_id = session.get("user_id")
    from models import notifications as notif_model
    notif_model.mark_as_read(notification_id, user_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"status": "success"}
    return redirect(url_for("citizen.notifications"))


@citizen_bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
@citizen_required
def mark_all_read():
    user_id = session.get("user_id")
    from models import notifications as notif_model
    notif_model.mark_all_as_read(user_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"status": "success"}
    flash("All notifications marked as read.", "success")
    return redirect(url_for("citizen.notifications"))


@citizen_bp.route("/feedback/<int:token_id>", methods=["GET", "POST"])
@login_required
@citizen_required
def feedback(token_id):
    user_id = session.get("user_id")
    token = token_model.get_token_by_id(token_id)

    if not token or token.get("user_id") != user_id:
        flash("Token not found or unauthorized.", "danger")
        return redirect(url_for("citizen.history"))

    if token.get("status") != "completed":
        flash("Feedback can only be submitted for completed services.", "warning")
        return redirect(url_for("citizen.history"))

    existing_feedback = feedback_model.get_feedback_by_token(token_id)

    if request.method == "POST":
        if existing_feedback:
            flash("Feedback has already been submitted for this token.", "info")
            return redirect(url_for("citizen.history"))

        rating = request.form.get("rating")
        comment = sanitize_input(request.form.get("comment", ""))

        success, message = feedback_model.add_feedback(
            user_id=user_id,
            token_id=token_id,
            rating=rating,
            comment=comment
        )
        if success:
            flash(message, "success")
            return redirect(url_for("citizen.history"))
        else:
            flash(message, "danger")

    return render_template(
        "citizen/feedback.html",
        token=token,
        existing_feedback=existing_feedback
    )
