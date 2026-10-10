"""Counter data access methods."""

from utils.db import execute_query


def get_counters_by_office(office_id, status=None):
    if status:
        query = """
            SELECT c.*, d.department_name, o.office_name
            FROM counters c
            JOIN departments d ON c.department_id = d.id
            JOIN offices o ON c.office_id = o.id
            WHERE c.office_id = %s AND c.status = %s
            ORDER BY c.counter_number
        """
        return execute_query(query, (office_id, status), fetch_all=True) or []

    query = """
        SELECT c.*, d.department_name, o.office_name
        FROM counters c
        JOIN departments d ON c.department_id = d.id
        JOIN offices o ON c.office_id = o.id
        WHERE c.office_id = %s
        ORDER BY c.counter_number
    """
    return execute_query(query, (office_id,), fetch_all=True) or []


def get_counters_by_department(department_id, status=None):
    if status:
        query = """
            SELECT c.*, d.department_name, o.office_name
            FROM counters c
            JOIN departments d ON c.department_id = d.id
            JOIN offices o ON c.office_id = o.id
            WHERE c.department_id = %s AND c.status = %s
            ORDER BY c.counter_number
        """
        return execute_query(query, (department_id, status), fetch_all=True) or []

    query = """
        SELECT c.*, d.department_name, o.office_name
        FROM counters c
        JOIN departments d ON c.department_id = d.id
        JOIN offices o ON c.office_id = o.id
        WHERE c.department_id = %s
        ORDER BY c.counter_number
    """
    return execute_query(query, (department_id,), fetch_all=True) or []


def get_all_counters(status=None):
    if status:
        query = """
            SELECT c.*, d.department_name, o.office_name
            FROM counters c
            JOIN departments d ON c.department_id = d.id
            JOIN offices o ON c.office_id = o.id
            WHERE c.status = %s
            ORDER BY o.office_name, c.counter_number
        """
        return execute_query(query, (status,), fetch_all=True) or []

    query = """
        SELECT c.*, d.department_name, o.office_name
        FROM counters c
        JOIN departments d ON c.department_id = d.id
        JOIN offices o ON c.office_id = o.id
        ORDER BY o.office_name, c.counter_number
    """
    return execute_query(query, fetch_all=True) or []


def get_counter_by_id(counter_id):
    query = "SELECT * FROM counters WHERE id = %s"
    return execute_query(query, (counter_id,), fetch_one=True)


def add_counter(office_id, department_id, counter_number, status="active"):
    query = """
        INSERT INTO counters (office_id, department_id, counter_number, status)
        VALUES (%s, %s, %s, %s)
    """
    return execute_query(
        query,
        (office_id, department_id, counter_number, status),
        commit=True,
    )


def update_counter(counter_id, office_id, department_id, counter_number, status):
    query = """
        UPDATE counters
        SET office_id = %s, department_id = %s, counter_number = %s, status = %s
        WHERE id = %s
    """
    return execute_query(
        query,
        (office_id, department_id, counter_number, status, counter_id),
        commit=True,
    )


def toggle_counter_status(counter_id):
    query = """
        UPDATE counters
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (counter_id,), commit=True)
