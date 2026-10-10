"""Token queue data access methods."""

from datetime import date
from utils.db import execute_query


def _generate_token_number(department_id, token_date):
    query = """
        SELECT COUNT(*) AS count
        FROM tokens
        WHERE department_id = %s AND token_date = %s
    """
    row = execute_query(query, (department_id, token_date), fetch_one=True)
    count = (row["count"] if row else 0) + 1
    # Use format A-001, A-002 based on department ID mod 26 or prefix
    dept_char = chr(65 + ((department_id - 1) % 26))
    return f"{dept_char}-{count:03d}"


def generate_token(user_id, office_id, department_id, service_id, token_date=None):
    token_date = token_date or date.today()

    # Prevent duplicate active token for the same user on the same service on the same date
    existing_query = """
        SELECT id FROM tokens
        WHERE user_id = %s AND service_id = %s AND token_date = %s
          AND status IN ('waiting', 'called', 'serving')
        LIMIT 1
    """
    existing = execute_query(
        existing_query,
        (user_id, service_id, token_date),
        fetch_one=True,
    )
    if existing:
        raise ValueError("You already have an active token for this service today.")

    token_number = _generate_token_number(department_id, token_date)

    query = """
        INSERT INTO tokens
            (token_number, user_id, office_id, department_id, service_id, token_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'waiting')
    """
    token_id = execute_query(
        query,
        (token_number, user_id, office_id, department_id, service_id, token_date),
        commit=True,
    )
    return {
        "id": token_id,
        "token_number": token_number,
        "token_date": token_date,
        "status": "waiting",
    }


def create_token(user_id, office_id, department_id, service_id, token_date=None):
    return generate_token(user_id, office_id, department_id, service_id, token_date)


def get_token_by_id(token_id):
    query = """
        SELECT t.*,
               u.full_name AS user_name,
               o.office_name,
               d.department_name,
               s.service_name,
               s.average_time,
               c.counter_number
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        WHERE t.id = %s
    """
    return execute_query(query, (token_id,), fetch_one=True)


def get_active_user_token(user_id):
    query = """
        SELECT t.*,
               o.office_name,
               d.department_name,
               s.service_name,
               s.average_time,
               c.counter_number
        FROM tokens t
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        WHERE t.user_id = %s AND t.status IN ('waiting', 'called', 'serving')
        ORDER BY t.created_at DESC
        LIMIT 1
    """
    return execute_query(query, (user_id,), fetch_one=True)


def get_queue_status_for_token(token_id):
    token = get_token_by_id(token_id)
    if not token:
        return None

    # Currently serving or called token for the service on the same token date
    serving_query = """
        SELECT token_number FROM tokens
        WHERE service_id = %s AND token_date = %s AND status IN ('serving', 'called')
        ORDER BY serving_at DESC, called_at DESC, id DESC
        LIMIT 1
    """
    serving_row = execute_query(
        serving_query,
        (token["service_id"], token["token_date"]),
        fetch_one=True,
    )
    current_token = serving_row["token_number"] if serving_row else "None"

    # People ahead in line (waiting status, earlier token ID for same service & date)
    ahead_query = """
        SELECT COUNT(*) AS count FROM tokens
        WHERE service_id = %s AND token_date = %s AND status = 'waiting' AND id < %s
    """
    ahead_row = execute_query(
        ahead_query,
        (token["service_id"], token["token_date"], token["id"]),
        fetch_one=True,
    )
    people_ahead = ahead_row["count"] if ahead_row else 0

    avg_time = token.get("average_time") or 15
    if token["status"] in ("serving", "called"):
        estimated_wait = 0
        people_ahead = 0
    else:
        estimated_wait = people_ahead * avg_time

    return {
        "token_id": token["id"],
        "user_token": token["token_number"],
        "current_token": current_token,
        "people_ahead": people_ahead,
        "estimated_wait": estimated_wait,
        "queue_status": token["status"],
        "office_name": token.get("office_name", ""),
        "department_name": token.get("department_name", ""),
        "service_name": token.get("service_name", ""),
        "counter_number": token.get("counter_number", "Unassigned"),
        "token_date": str(token["token_date"]),
        "created_at": str(token.get("created_at", "")),
    }


def cancel_token(token_id, user_id):
    query = """
        UPDATE tokens
        SET status = 'cancelled'
        WHERE id = %s AND user_id = %s AND status = 'waiting'
    """
    return execute_query(query, (token_id, user_id), commit=True)


def get_user_token_history(user_id, limit=50):
    query = """
        SELECT t.*, o.office_name, d.department_name, s.service_name, c.counter_number,
               f.id AS feedback_id, f.rating AS feedback_rating, f.comment AS feedback_comment
        FROM tokens t
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        LEFT JOIN feedback f ON t.id = f.token_id
        WHERE t.user_id = %s
        ORDER BY t.created_at DESC
        LIMIT %s
    """
    return execute_query(query, (user_id, limit), fetch_all=True) or []


def get_tokens_by_user(user_id, limit=20):
    return get_user_token_history(user_id, limit=limit)


def get_tokens_by_office(office_id, token_date=None, status=None):
    token_date = token_date or date.today()
    params = [office_id, token_date]

    query = """
        SELECT t.*, u.full_name AS user_name, d.department_name, s.service_name
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        WHERE t.office_id = %s AND t.token_date = %s
    """
    if status:
        query += " AND t.status = %s"
        params.append(status)

    query += " ORDER BY t.created_at ASC"
    return execute_query(query, tuple(params), fetch_all=True) or []


def get_waiting_tokens(department_id, token_date=None):
    token_date = token_date or date.today()
    query = """
        SELECT t.*, u.full_name AS user_name, s.service_name
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN services s ON t.service_id = s.id
        WHERE t.department_id = %s
          AND t.token_date = %s
          AND t.status = 'waiting'
        ORDER BY t.created_at ASC
    """
    return execute_query(query, (department_id, token_date), fetch_all=True) or []


def get_staff_counter_queue(office_id, department_id, token_date=None):
    """Get list of waiting tokens for today for the staff member's department & office."""
    token_date = token_date or date.today()
    query = """
        SELECT t.*, u.full_name AS user_name, s.service_name
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN services s ON t.service_id = s.id
        WHERE t.office_id = %s AND t.department_id = %s
          AND t.token_date = %s AND t.status = 'waiting'
        ORDER BY t.created_at ASC
    """
    return execute_query(query, (office_id, department_id, token_date), fetch_all=True) or []


def get_current_counter_token(counter_id, token_date=None):
    """Get token currently with status 'called' or 'serving' at this counter today."""
    if not counter_id:
        return None
    token_date = token_date or date.today()
    query = """
        SELECT t.*,
               u.full_name AS user_name,
               o.office_name,
               d.department_name,
               s.service_name,
               c.counter_number
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        WHERE t.counter_id = %s AND t.token_date = %s AND t.status IN ('called', 'serving')
        ORDER BY t.called_at DESC, t.serving_at DESC, t.id DESC
        LIMIT 1
    """
    return execute_query(query, (counter_id, token_date), fetch_one=True)


def call_next_token(staff_id, counter_id, office_id, department_id, token_date=None):
    """Pick earliest waiting token for today, set status to CALLED, update counter_id and called_at."""
    token_date = token_date or date.today()
    find_query = """
        SELECT id FROM tokens
        WHERE office_id = %s AND department_id = %s AND token_date = %s AND status = 'waiting'
        ORDER BY created_at ASC
        LIMIT 1
    """
    row = execute_query(find_query, (office_id, department_id, token_date), fetch_one=True)
    if not row:
        return None

    token_id = row["id"]
    update_query = """
        UPDATE tokens
        SET status = 'called',
            counter_id = %s,
            called_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(update_query, (counter_id, token_id), commit=True)
    called_token = get_token_by_id(token_id)
    
    # --- Trigger Notifications ---
    from models.notifications import create_notification
    # 1. Notify CALLED
    if called_token:
        create_notification(
            user_id=called_token['user_id'],
            token_id=called_token['id'],
            title="It's your turn!",
            message=f"It's your turn! Token {called_token['token_number']} is called at Counter {called_token['counter_number']}.",
            type="token_update"
        )
        
    # 2. Notify 2 people ahead (index 1 in the remaining waiting queue)
    queue = get_staff_counter_queue(office_id, department_id, token_date)
    if len(queue) > 1:
        near_token = queue[1] # 2nd person in waiting queue
        counter_num = called_token['counter_number'] if called_token else "your assigned counter"
        create_notification(
            user_id=near_token['user_id'],
            token_id=near_token['id'],
            title="Your turn is near!",
            message=f"Your turn is near! Token {near_token['token_number']} will be called soon. Please reach Counter {counter_num}.",
            type="info"
        )
        
    return called_token


def start_serving_token(token_id):
    """Update status to SERVING and set serving_at timestamp."""
    query = """
        UPDATE tokens
        SET status = 'serving',
            serving_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(query, (token_id,), commit=True)
    return get_token_by_id(token_id)


def complete_token(token_id):
    """Update status to COMPLETED and set completed_at timestamp."""
    query = """
        UPDATE tokens
        SET status = 'completed',
            completed_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(query, (token_id,), commit=True)
    return get_token_by_id(token_id)


def skip_token(token_id):
    """Update status to no_show / skipped."""
    query = """
        UPDATE tokens
        SET status = 'no_show'
        WHERE id = %s
    """
    execute_query(query, (token_id,), commit=True)
    
    skipped_token = get_token_by_id(token_id)
    if skipped_token:
        from models.notifications import create_notification
        create_notification(
            user_id=skipped_token['user_id'],
            token_id=skipped_token['id'],
            title="Token Skipped",
            message=f"Your token {skipped_token['token_number']} was skipped. Please contact counter staff.",
            type="warning"
        )
        
    return skipped_token


def recall_token(token_id):
    """Set status back to CALLED to notify citizen again."""
    query = """
        UPDATE tokens
        SET status = 'called',
            called_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(query, (token_id,), commit=True)
    return get_token_by_id(token_id)


def get_staff_history(counter_id, token_date=None):
    """Fetch today's completed, skipped, or processed tokens for this counter."""
    if not counter_id:
        return []
    token_date = token_date or date.today()
    query = """
        SELECT t.*, u.full_name AS user_name, s.service_name
        FROM tokens t
        JOIN users u ON t.user_id = u.id
        JOIN services s ON t.service_id = s.id
        WHERE t.counter_id = %s AND t.token_date = %s
        ORDER BY t.created_at DESC
        LIMIT 50
    """
    return execute_query(query, (counter_id, token_date), fetch_all=True) or []


def update_token_status(token_id, status, counter_id=None):
    timestamp_field = {
        "called": "called_at",
        "serving": "serving_at",
        "completed": "completed_at",
    }.get(status)

    if timestamp_field:
        query = f"""
            UPDATE tokens
            SET status = %s,
                counter_id = COALESCE(%s, counter_id),
                {timestamp_field} = CURRENT_TIMESTAMP
            WHERE id = %s
        """
    else:
        query = """
            UPDATE tokens
            SET status = %s, counter_id = COALESCE(%s, counter_id)
            WHERE id = %s
        """

    return execute_query(query, (status, counter_id, token_id), commit=True)


def count_tokens_today(service_id, token_date=None):
    token_date = token_date or date.today()
    query = """
        SELECT COUNT(*) AS count
        FROM tokens
        WHERE service_id = %s AND token_date = %s AND status != 'cancelled'
    """
    row = execute_query(query, (service_id, token_date), fetch_one=True)
    return row["count"] if row else 0


def get_office_display_data(office_id):
    """Fetch active called/serving, waiting, and overview metrics for the office display board."""
    today = date.today()
    serving_query = """
        SELECT t.id, t.token_number, t.status, t.called_at, t.serving_at,
               COALESCE(c.counter_number, 'Counter') AS counter_number,
               d.department_name, s.service_name,
               u.full_name AS citizen_name
        FROM tokens t
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        LEFT JOIN counters c ON t.counter_id = c.id
        JOIN users u ON t.user_id = u.id
        WHERE t.office_id = %s AND t.token_date = %s
          AND t.status IN ('called', 'serving')
        ORDER BY CASE WHEN t.status = 'called' THEN 1 ELSE 2 END,
                 t.called_at DESC, t.serving_at DESC
        LIMIT 12
    """
    now_serving = execute_query(serving_query, (office_id, today), fetch_all=True) or []

    for item in now_serving:
        name_parts = (item.get("citizen_name") or "Citizen").split()
        masked_parts = [p[0] + "*" * min(4, max(1, len(p) - 1)) if len(p) > 1 else p for p in name_parts]
        item["masked_name"] = " ".join(masked_parts)
        if item.get("called_at"):
            item["called_at_str"] = str(item["called_at"]).split(".")[0]
        if item.get("serving_at"):
            item["serving_at_str"] = str(item["serving_at"]).split(".")[0]

    waiting_query = """
        SELECT t.id, t.token_number, t.status, t.created_at,
               d.department_name, s.service_name, s.average_time
        FROM tokens t
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        WHERE t.office_id = %s AND t.token_date = %s
          AND t.status = 'waiting'
        ORDER BY t.created_at ASC
        LIMIT 15
    """
    waiting = execute_query(waiting_query, (office_id, today), fetch_all=True) or []
    for idx, item in enumerate(waiting):
        item["position"] = idx + 1
        avg_time = item.get("average_time") or 15
        item["est_wait"] = idx * avg_time

    stats_query = """
        SELECT
            COUNT(*) AS total_today,
            SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END) AS total_waiting,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS total_completed,
            SUM(CASE WHEN status IN ('called', 'serving') THEN 1 ELSE 0 END) AS total_active
        FROM tokens
        WHERE office_id = %s AND token_date = %s
    """
    stats_row = execute_query(stats_query, (office_id, today), fetch_one=True) or {}

    return {
        "now_serving": now_serving,
        "waiting_queue": waiting,
        "stats": {
            "total_today": int(stats_row.get("total_today") or 0),
            "total_waiting": int(stats_row.get("total_waiting") or 0),
            "total_completed": int(stats_row.get("total_completed") or 0),
            "total_active": int(stats_row.get("total_active") or 0),
        }
    }


# Analytics and reports aliases from models.admin
from models.admin import (
    get_tokens_per_day_chart,
    get_service_usage_chart,
    get_department_queue_chart,
    get_status_breakdown_chart,
    get_filtered_reports,
)

