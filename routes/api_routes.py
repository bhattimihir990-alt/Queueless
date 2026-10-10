from flask import Blueprint, jsonify, request

from models import token as token_model
from models import appointment as appointment_model

api_bp = Blueprint("api", __name__)


@api_bp.route("/queue/<int:token_id>")
def queue_status_api(token_id):
    queue_status = token_model.get_queue_status_for_token(token_id)
    if not queue_status:
        return jsonify({"error": "Token not found"}), 404

    return jsonify(queue_status)


@api_bp.route("/slots")
def get_slots():
    service_id = request.args.get("service_id", type=int)
    date_str = request.args.get("date")
    
    if not service_id or not date_str:
        return jsonify({"status": "error", "message": "Missing parameters", "slots": []}), 400
        
    slots = appointment_model.get_available_slots(service_id, date_str)
    return jsonify({"status": "success", "slots": slots})


@api_bp.route("/notifications/unread-count")
def unread_count():
    from utils.auth import session
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"unread_count": 0}), 401
    
    from models import notifications as notif_model
    count = notif_model.get_unread_count(user_id)
    return jsonify({"unread_count": count})


@api_bp.route("/admin/chart-data")
def admin_chart_data():
    from utils.auth import session
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    from models import admin as admin_model
    data = admin_model.get_all_charts_data()
    return jsonify({"status": "success", "data": data})


@api_bp.route("/queue/display-data/<int:office_id>")
def queue_display_data(office_id):
    from datetime import datetime
    data = token_model.get_office_display_data(office_id)
    data["server_time"] = datetime.now().strftime("%I:%M:%S %p")
    return jsonify({"status": "success", **data})


@api_bp.route("/staff/live-queue")
def staff_live_queue():
    from utils.auth import session
    if not session.get("logged_in") or session.get("role") != "staff":
        return jsonify({"error": "Unauthorized"}), 403

    from models import staff as staff_model
    staff_id = session.get("user_id")
    staff_info = staff_model.get_staff_assignment_details(staff_id)
    if not staff_info:
        return jsonify({"error": "Staff profile not found"}), 404

    counter_id = staff_info.get("counter_id")
    office_id = staff_info.get("office_id")
    dept_id = staff_info.get("department_id")

    current_token = token_model.get_current_counter_token(counter_id) if counter_id else None
    waiting_queue = token_model.get_staff_counter_queue(office_id, dept_id) if (office_id and dept_id) else []
    next_token = waiting_queue[0] if waiting_queue else None

    # Format dates/timestamps as strings for JSON serialization
    def serialize_token(tok):
        if not tok:
            return None
        t = dict(tok)
        for k in ("created_at", "called_at", "serving_at", "completed_at", "token_date"):
            if t.get(k):
                t[k] = str(t[k])
        return t

    return jsonify({
        "status": "success",
        "staff_info": {
            "name": staff_info.get("name"),
            "office_name": staff_info.get("office_name"),
            "department_name": staff_info.get("department_name"),
            "counter_number": staff_info.get("counter_number") or "Unassigned",
        },
        "current_token": serialize_token(current_token),
        "next_token": serialize_token(next_token),
        "waiting_queue": [serialize_token(t) for t in waiting_queue],
        "waiting_count": len(waiting_queue),
    })


@api_bp.route("/admin/live-metrics")
def admin_live_metrics():
    from utils.auth import session
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    from models import admin as admin_model
    stats = admin_model.get_admin_dashboard_stats()
    chart_data = admin_model.get_all_charts_data()
    return jsonify({
        "status": "success",
        "stats": stats,
        "charts": chart_data,
    })


@api_bp.route("/departments")
def api_departments():
    office_id = request.args.get("office_id", type=int)
    from models import department as department_model
    if office_id:
        depts = department_model.get_departments_by_office(office_id, status="active")
    else:
        depts = department_model.get_all_departments(status="active")
    return jsonify({"status": "success", "departments": depts})


@api_bp.route("/counters")
def api_counters():
    dept_id = request.args.get("department_id", type=int)
    office_id = request.args.get("office_id", type=int)
    from models import counter as counter_model
    if dept_id:
        counters = counter_model.get_counters_by_department(dept_id, status="active")
    elif office_id:
        counters = counter_model.get_counters_by_office(office_id, status="active")
    else:
        counters = counter_model.get_all_counters(status="active")
    return jsonify({"status": "success", "counters": counters})


