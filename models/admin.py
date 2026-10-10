"""Admin data access methods and analytics queries."""

from datetime import date, timedelta
from utils.auth import hash_password
from utils.db import execute_query


def get_admin_by_id(admin_id):
    query = "SELECT * FROM admins WHERE id = %s"
    return execute_query(query, (admin_id,), fetch_one=True)


def get_admin_by_email(email):
    query = "SELECT * FROM admins WHERE email = %s"
    return execute_query(query, (email,), fetch_one=True)


def get_admin_by_username(username):
    if not username:
        return None
    query = "SELECT * FROM admins WHERE username = %s"
    return execute_query(query, (username,), fetch_one=True)


def get_admin_by_identifier(identifier):
    if not identifier:
        return None
    query = "SELECT * FROM admins WHERE email = %s OR username = %s LIMIT 1"
    return execute_query(query, (identifier, identifier), fetch_one=True)


def get_all_admins():
    query = "SELECT id, name, username, email, status, created_at FROM admins ORDER BY id ASC"
    return execute_query(query, fetch_all=True) or []


def create_admin(name, email, raw_password, username=None, status="active"):
    password_hash = hash_password(raw_password)
    query = """
        INSERT INTO admins (name, username, email, password_hash, status)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(
        query,
        (name, username, email, password_hash, status),
        commit=True,
    )


def get_admin_dashboard_stats():
    query = """
        SELECT
            (SELECT COUNT(*) FROM offices) AS total_offices,
            (SELECT COUNT(*) FROM staff WHERE status = 'active') AS total_staff,
            (SELECT COUNT(*) FROM tokens WHERE token_date = CURDATE()) AS today_tokens,
            (SELECT COUNT(*) FROM users WHERE status = 'active') AS active_citizens,
            (SELECT COUNT(*) FROM tokens
             WHERE token_date = CURDATE() AND status = 'waiting') AS waiting_tokens,
            (SELECT COUNT(*) FROM tokens
             WHERE token_date = CURDATE() AND status = 'completed') AS completed_tokens,
            (SELECT COUNT(*) FROM users) AS total_citizens,
            (SELECT COUNT(*) FROM departments WHERE status = 'active') AS total_departments,
            (SELECT COUNT(*) FROM services WHERE status = 'active') AS total_services
    """
    stats = execute_query(query, fetch_one=True)
    return stats or {
        "total_offices": 0,
        "total_staff": 0,
        "today_tokens": 0,
        "active_citizens": 0,
        "waiting_tokens": 0,
        "completed_tokens": 0,
        "total_citizens": 0,
        "total_departments": 0,
        "total_services": 0,
    }


def get_tokens_per_day_chart():
    """Fetch daily token generation counts for the last 7 days."""
    today = date.today()
    start_date = today - timedelta(days=6)
    query = """
        SELECT token_date, COUNT(*) AS count
        FROM tokens
        WHERE token_date BETWEEN %s AND %s
        GROUP BY token_date
        ORDER BY token_date ASC
    """
    rows = execute_query(query, (start_date, today), fetch_all=True) or []
    counts_by_date = {str(r["token_date"]): r["count"] for r in rows}

    labels = []
    data = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        labels.append(d.strftime("%b %d"))
        data.append(counts_by_date.get(str(d), 0))

    return {"labels": labels, "data": data}


def get_service_usage_chart():
    """Fetch total tokens generated per service."""
    query = """
        SELECT s.service_name, COUNT(t.id) AS count
        FROM services s
        JOIN tokens t ON s.id = t.service_id
        GROUP BY s.id, s.service_name
        ORDER BY count DESC
        LIMIT 8
    """
    rows = execute_query(query, fetch_all=True) or []
    if not rows:
        return {"labels": ["No Services Used"], "data": [0]}
    labels = [r["service_name"] for r in rows]
    data = [r["count"] for r in rows]
    return {"labels": labels, "data": data}


def get_department_queue_chart():
    """Fetch active waiting tokens per department."""
    query = """
        SELECT d.department_name,
               SUM(CASE WHEN t.status = 'waiting' AND t.token_date = CURDATE() THEN 1 ELSE 0 END) AS waiting_count,
               COUNT(t.id) AS total_today
        FROM departments d
        LEFT JOIN tokens t ON d.id = t.department_id AND t.token_date = CURDATE()
        GROUP BY d.id, d.department_name
        ORDER BY waiting_count DESC, total_today DESC
        LIMIT 8
    """
    rows = execute_query(query, fetch_all=True) or []
    labels = [r["department_name"] for r in rows] or ["No Departments"]
    data = [int(r["waiting_count"] or 0) for r in rows] or [0]
    return {"labels": labels, "data": data}


def get_status_breakdown_chart():
    """Fetch count breakdown by status (COMPLETED, SKIPPED, CANCELLED, WAITING, SERVING)."""
    query = """
        SELECT status, COUNT(*) AS count
        FROM tokens
        GROUP BY status
    """
    rows = execute_query(query, fetch_all=True) or []
    status_counts = {r["status"]: r["count"] for r in rows}

    mapping = [
        ("Completed", status_counts.get("completed", 0)),
        ("Waiting", status_counts.get("waiting", 0)),
        ("Serving / Called", status_counts.get("serving", 0) + status_counts.get("called", 0)),
        ("Skipped", status_counts.get("no_show", 0)),
        ("Cancelled", status_counts.get("cancelled", 0)),
    ]
    labels = [m[0] for m in mapping]
    data = [m[1] for m in mapping]
    return {"labels": labels, "data": data}


def get_all_charts_data():
    """Aggregated JSON object for all Chart.js visualizations."""
    return {
        "tokens_per_day": get_tokens_per_day_chart(),
        "service_usage": get_service_usage_chart(),
        "department_queue": get_department_queue_chart(),
        "status_breakdown": get_status_breakdown_chart(),
    }


def get_filtered_reports(office_id=None, department_id=None, service_id=None, status=None, start_date=None, end_date=None):
    """Query detailed token logs based on date range and filter criteria."""
    query = """
        SELECT t.id, t.token_number, t.token_date, t.status,
               t.created_at, t.called_at, t.serving_at, t.completed_at,
               u.full_name AS citizen_name, u.mobile AS citizen_mobile,
               o.id AS office_id, o.office_name,
               d.id AS department_id, d.department_name,
               s.id AS service_id, s.service_name,
               COALESCE(c.counter_number, '—') AS counter_number
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        WHERE 1=1
    """
    params = []
    if office_id:
        query += " AND o.id = %s"
        params.append(office_id)
    if department_id:
        query += " AND d.id = %s"
        params.append(department_id)
    if service_id:
        query += " AND s.id = %s"
        params.append(service_id)
    if status:
        query += " AND t.status = %s"
        params.append(status)
    if start_date:
        query += " AND t.token_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND t.token_date <= %s"
        params.append(end_date)

    query += " ORDER BY t.token_date DESC, t.id DESC"
    return execute_query(query, tuple(params), fetch_all=True) or []
