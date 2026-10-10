"""Feedback and Rating data access methods."""

from utils.db import execute_query


def add_feedback(user_id, token_id, rating, comment=""):
    """
    Insert a new feedback entry linked to a completed token.
    Prevents duplicate submissions for the same token.
    """
    # 1. Verify token exists, belongs to user, and is completed
    token_query = """
        SELECT id, user_id, status
        FROM tokens
        WHERE id = %s
    """
    token = execute_query(token_query, (token_id,), fetch_one=True)
    if not token:
        return False, "Token not found."

    if token["user_id"] != user_id:
        return False, "You can only submit feedback for your own tokens."

    if token["status"] != "completed":
        return False, "Feedback can only be submitted for completed tokens."

    # 2. Check for duplicate feedback
    existing_query = "SELECT id FROM feedback WHERE token_id = %s"
    existing = execute_query(existing_query, (token_id,), fetch_one=True)
    if existing:
        return False, "Feedback has already been submitted for this token."

    # 3. Validate rating range (1-5)
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            return False, "Rating must be between 1 and 5 stars."
    except (TypeError, ValueError):
        return False, "Invalid rating value."

    comment_clean = (comment or "").strip()

    insert_query = """
        INSERT INTO feedback (user_id, token_id, rating, comment)
        VALUES (%s, %s, %s, %s)
    """
    success = execute_query(
        insert_query,
        (user_id, token_id, rating_int, comment_clean),
        commit=True
    )
    if success:
        return True, "Thank you! Your feedback has been submitted successfully."
    return False, "Failed to submit feedback. Please try again."


def get_feedback_by_token(token_id):
    """Fetch existing feedback entry for a specific token."""
    query = """
        SELECT *
        FROM feedback
        WHERE token_id = %s
    """
    return execute_query(query, (token_id,), fetch_one=True)


def get_user_feedback(user_id):
    """Fetch all past feedback submitted by a specific citizen."""
    query = """
        SELECT f.*,
               t.token_number,
               t.token_date,
               o.office_name,
               d.department_name,
               s.service_name
        FROM feedback f
        JOIN tokens t ON f.token_id = t.id
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        WHERE f.user_id = %s
        ORDER BY f.created_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def get_all_feedback_admin(office_id=None, service_id=None, rating=None):
    """
    Fetch all feedback with citizen and service details for Admin panel.
    Supports optional filtering by office, service, or rating.
    """
    query = """
        SELECT f.*,
               u.full_name AS citizen_name,
               u.mobile AS citizen_mobile,
               u.email AS citizen_email,
               t.token_number,
               t.token_date,
               o.id AS office_id,
               o.office_name,
               d.department_name,
               s.id AS service_id,
               s.service_name
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        JOIN tokens t ON f.token_id = t.id
        JOIN offices o ON t.office_id = o.id
        JOIN departments d ON t.department_id = d.id
        JOIN services s ON t.service_id = s.id
        WHERE 1=1
    """
    params = []
    if office_id:
        query += " AND o.id = %s"
        params.append(office_id)
    if service_id:
        query += " AND s.id = %s"
        params.append(service_id)
    if rating:
        query += " AND f.rating = %s"
        params.append(rating)

    query += " ORDER BY f.created_at DESC"
    return execute_query(query, tuple(params), fetch_all=True) or []


def get_service_rating_summary():
    """
    Calculate average rating and total review counts grouped by service and office.
    """
    query = """
        SELECT s.id AS service_id,
               s.service_name,
               o.id AS office_id,
               o.office_name,
               d.department_name,
               COUNT(f.id) AS total_reviews,
               ROUND(AVG(f.rating), 1) AS avg_rating,
               SUM(CASE WHEN f.rating = 5 THEN 1 ELSE 0 END) AS count_5,
               SUM(CASE WHEN f.rating = 4 THEN 1 ELSE 0 END) AS count_4,
               SUM(CASE WHEN f.rating = 3 THEN 1 ELSE 0 END) AS count_3,
               SUM(CASE WHEN f.rating = 2 THEN 1 ELSE 0 END) AS count_2,
               SUM(CASE WHEN f.rating = 1 THEN 1 ELSE 0 END) AS count_1
        FROM feedback f
        JOIN tokens t ON f.token_id = t.id
        JOIN services s ON t.service_id = s.id
        JOIN departments d ON s.department_id = d.id
        JOIN offices o ON d.office_id = o.id
        GROUP BY s.id, s.service_name, o.id, o.office_name, d.department_name
        ORDER BY avg_rating DESC, total_reviews DESC
    """
    return execute_query(query, fetch_all=True) or []


def get_overall_feedback_stats():
    """Calculate high-level KPI metrics for Admin feedback dashboard."""
    query = """
        SELECT COUNT(f.id) AS total_feedback,
               ROUND(AVG(f.rating), 1) AS avg_rating,
               SUM(CASE WHEN f.rating >= 4 THEN 1 ELSE 0 END) AS positive_count,
               COUNT(DISTINCT t.service_id) AS services_rated
        FROM feedback f
        JOIN tokens t ON f.token_id = t.id
    """
    row = execute_query(query, fetch_one=True)
    if not row or not row["total_feedback"]:
        return {
            "total_feedback": 0,
            "avg_rating": 0.0,
            "positive_pct": 0,
            "services_rated": 0,
        }

    total = row["total_feedback"]
    positive = row["positive_count"] or 0
    pos_pct = round((positive / total) * 100) if total > 0 else 0

    return {
        "total_feedback": total,
        "avg_rating": float(row["avg_rating"] or 0.0),
        "positive_pct": pos_pct,
        "services_rated": row["services_rated"] or 0,
    }
