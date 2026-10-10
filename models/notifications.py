"""Notification data access methods."""

from utils.db import execute_query

def create_notification(user_id, token_id, title, message, type='info'):
    query = """
        INSERT INTO notifications (user_id, token_id, title, message, type)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (user_id, token_id, title, message, type), commit=True)


def get_user_notifications(user_id):
    query = """
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def mark_as_read(notification_id, user_id):
    query = """
        UPDATE notifications
        SET is_read = 1
        WHERE id = %s AND user_id = %s
    """
    return execute_query(query, (notification_id, user_id), commit=True)


def mark_all_as_read(user_id):
    query = """
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = %s AND is_read = 0
    """
    return execute_query(query, (user_id,), commit=True)


def get_unread_count(user_id):
    query = """
        SELECT COUNT(*) as count
        FROM notifications
        WHERE user_id = %s AND is_read = 0
    """
    result = execute_query(query, (user_id,), fetch_one=True)
    return result['count'] if result else 0
