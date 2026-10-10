"""User (citizen) data access methods."""

from utils.auth import hash_password
from utils.db import execute_query


def create_user(name, mobile, email, raw_password, address=None, status="active"):
    password_hash = hash_password(raw_password)
    query = """
        INSERT INTO users (full_name, mobile, email, password_hash, address, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(
        query,
        (name, mobile, email, password_hash, address, status),
        commit=True,
    )


def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    return execute_query(query, (user_id,), fetch_one=True)


def get_user_by_email(email):
    query = "SELECT * FROM users WHERE email = %s"
    return execute_query(query, (email,), fetch_one=True)


def get_user_by_mobile(mobile):
    query = "SELECT * FROM users WHERE mobile = %s"
    return execute_query(query, (mobile,), fetch_one=True)


def get_all_citizens(status=None, limit=200, offset=0):
    if status:
        query = """
            SELECT id, full_name, mobile, email, address, status, created_at
            FROM users
            WHERE status = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return execute_query(query, (status, limit, offset), fetch_all=True) or []

    query = """
        SELECT id, full_name, mobile, email, address, status, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    return execute_query(query, (limit, offset), fetch_all=True) or []


def toggle_citizen_status(user_id):
    query = """
        UPDATE users
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (user_id,), commit=True)


def update_user_status(user_id, status):
    query = "UPDATE users SET status = %s WHERE id = %s"
    return execute_query(query, (status, user_id), commit=True)


def update_user_profile(user_id, full_name=None, mobile=None, email=None, address=None):
    fields = []
    params = []

    if full_name is not None:
        fields.append("full_name = %s")
        params.append(full_name)
    if mobile is not None:
        fields.append("mobile = %s")
        params.append(mobile)
    if email is not None:
        fields.append("email = %s")
        params.append(email)
    if address is not None:
        fields.append("address = %s")
        params.append(address)

    if not fields:
        return 0

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    return execute_query(query, tuple(params), commit=True)


def list_users(status=None, limit=50, offset=0):
    return get_all_citizens(status=status, limit=limit, offset=offset)
