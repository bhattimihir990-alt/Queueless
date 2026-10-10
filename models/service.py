"""Service data access methods."""

from utils.db import execute_query


def get_services_by_department(department_id, status=None):
    if status:
        query = """
            SELECT s.*, d.department_name, o.office_name
            FROM services s
            JOIN departments d ON s.department_id = d.id
            JOIN offices o ON d.office_id = o.id
            WHERE s.department_id = %s AND s.status = %s
            ORDER BY s.service_name
        """
        return execute_query(query, (department_id, status), fetch_all=True) or []

    query = """
        SELECT s.*, d.department_name, o.office_name
        FROM services s
        JOIN departments d ON s.department_id = d.id
        JOIN offices o ON d.office_id = o.id
        WHERE s.department_id = %s
        ORDER BY s.service_name
    """
    return execute_query(query, (department_id,), fetch_all=True) or []


def get_all_services(status=None):
    if status:
        query = """
            SELECT s.*, d.department_name, o.office_name, o.id AS office_id
            FROM services s
            JOIN departments d ON s.department_id = d.id
            JOIN offices o ON d.office_id = o.id
            WHERE s.status = %s
            ORDER BY o.office_name, d.department_name, s.service_name
        """
        return execute_query(query, (status,), fetch_all=True) or []

    query = """
        SELECT s.*, d.department_name, o.office_name, o.id AS office_id
        FROM services s
        JOIN departments d ON s.department_id = d.id
        JOIN offices o ON d.office_id = o.id
        ORDER BY o.office_name, d.department_name, s.service_name
    """
    return execute_query(query, fetch_all=True) or []


def get_service_by_id(service_id):
    query = "SELECT * FROM services WHERE id = %s"
    return execute_query(query, (service_id,), fetch_one=True)


def add_service(
    department_id,
    service_name,
    description,
    average_time,
    daily_limit,
    status="active",
):
    query = """
        INSERT INTO services
            (department_id, service_name, description, average_time, daily_limit, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(
        query,
        (department_id, service_name, description, average_time, daily_limit, status),
        commit=True,
    )


def update_service(
    service_id,
    department_id,
    service_name,
    description,
    average_time,
    daily_limit,
    status,
):
    query = """
        UPDATE services
        SET department_id = %s, service_name = %s, description = %s,
            average_time = %s, daily_limit = %s, status = %s
        WHERE id = %s
    """
    return execute_query(
        query,
        (department_id, service_name, description, average_time, daily_limit, status, service_id),
        commit=True,
    )


def toggle_service_status(service_id):
    query = """
        UPDATE services
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (service_id,), commit=True)
