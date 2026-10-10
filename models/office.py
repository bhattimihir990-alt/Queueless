"""Office data access methods."""

from utils.db import execute_query


def get_all_offices(status=None):
    if status:
        query = """
            SELECT id, office_name, address, city, phone,
                   opening_time, closing_time, status, created_at
            FROM offices
            WHERE status = %s
            ORDER BY office_name
        """
        return execute_query(query, (status,), fetch_all=True) or []

    query = """
        SELECT id, office_name, address, city, phone,
               opening_time, closing_time, status, created_at
        FROM offices
        ORDER BY office_name
    """
    return execute_query(query, fetch_all=True) or []


def get_office_by_id(office_id):
    query = "SELECT * FROM offices WHERE id = %s"
    return execute_query(query, (office_id,), fetch_one=True)


def add_office(office_name, address, city, phone, opening_time, closing_time, status="active"):
    query = """
        INSERT INTO offices
            (office_name, address, city, phone, opening_time, closing_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(
        query,
        (office_name, address, city, phone, opening_time, closing_time, status),
        commit=True,
    )


def update_office(
    office_id,
    office_name,
    address,
    city,
    phone,
    opening_time,
    closing_time,
    status,
):
    query = """
        UPDATE offices
        SET office_name = %s, address = %s, city = %s, phone = %s,
            opening_time = %s, closing_time = %s, status = %s
        WHERE id = %s
    """
    return execute_query(
        query,
        (office_name, address, city, phone, opening_time, closing_time, status, office_id),
        commit=True,
    )


def toggle_office_status(office_id):
    query = """
        UPDATE offices
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (office_id,), commit=True)


def get_office_hierarchy(office_id):
    """Return office with nested departments, services, and counters."""
    from models.counter import get_counters_by_department
    from models.department import get_departments_by_office
    from models.service import get_services_by_department

    office = get_office_by_id(office_id)
    if not office:
        return None

    departments = get_departments_by_office(office_id, status="active")
    for dept in departments:
        dept["services"] = get_services_by_department(dept["id"], status="active")
        dept["counters"] = get_counters_by_department(dept["id"], status="active")

    office["departments"] = departments
    return office
