"""Department data access methods."""

from utils.db import execute_query


def get_departments_by_office(office_id, status=None):
    if status:
        query = """
            SELECT d.*, o.office_name
            FROM departments d
            JOIN offices o ON d.office_id = o.id
            WHERE d.office_id = %s AND d.status = %s
            ORDER BY d.department_name
        """
        return execute_query(query, (office_id, status), fetch_all=True) or []

    query = """
        SELECT d.*, o.office_name
        FROM departments d
        JOIN offices o ON d.office_id = o.id
        WHERE d.office_id = %s
        ORDER BY d.department_name
    """
    return execute_query(query, (office_id,), fetch_all=True) or []


def get_all_departments(status=None):
    if status:
        query = """
            SELECT d.*, o.office_name
            FROM departments d
            JOIN offices o ON d.office_id = o.id
            WHERE d.status = %s
            ORDER BY o.office_name, d.department_name
        """
        return execute_query(query, (status,), fetch_all=True) or []

    query = """
        SELECT d.*, o.office_name
        FROM departments d
        JOIN offices o ON d.office_id = o.id
        ORDER BY o.office_name, d.department_name
    """
    return execute_query(query, fetch_all=True) or []


def get_department_by_id(department_id):
    query = """
        SELECT d.*, o.office_name
        FROM departments d
        JOIN offices o ON d.office_id = o.id
        WHERE d.id = %s
    """
    return execute_query(query, (department_id,), fetch_one=True)


def add_department(office_id, department_name, description=None, status="active"):
    query = """
        INSERT INTO departments (office_id, department_name, description, status)
        VALUES (%s, %s, %s, %s)
    """
    return execute_query(
        query,
        (office_id, department_name, description, status),
        commit=True,
    )


def update_department(department_id, office_id, department_name, description, status):
    query = """
        UPDATE departments
        SET office_id = %s, department_name = %s, description = %s, status = %s
        WHERE id = %s
    """
    return execute_query(
        query,
        (office_id, department_name, description, status, department_id),
        commit=True,
    )


def toggle_department_status(department_id):
    query = """
        UPDATE departments
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (department_id,), commit=True)
