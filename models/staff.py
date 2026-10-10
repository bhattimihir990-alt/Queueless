"""Staff data access methods."""

from utils.auth import hash_password
from utils.db import execute_query


def get_all_staff(status=None):
    if status:
        query = """
            SELECT st.*, o.office_name, d.department_name, c.counter_number
            FROM staff st
            JOIN offices o ON st.office_id = o.id
            JOIN departments d ON st.department_id = d.id
            LEFT JOIN counters c ON st.counter_id = c.id
            WHERE st.status = %s
            ORDER BY o.office_name, st.name
        """
        return execute_query(query, (status,), fetch_all=True) or []

    query = """
        SELECT st.*, o.office_name, d.department_name, c.counter_number
        FROM staff st
        JOIN offices o ON st.office_id = o.id
        JOIN departments d ON st.department_id = d.id
        LEFT JOIN counters c ON st.counter_id = c.id
        ORDER BY o.office_name, st.name
    """
    return execute_query(query, fetch_all=True) or []


def add_staff(
    office_id,
    department_id,
    name,
    mobile,
    email,
    raw_password,
    counter_id=None,
    status="active",
    username=None,
):
    password_hash = hash_password(raw_password)
    query = """
        INSERT INTO staff
            (office_id, department_id, counter_id, name, username, mobile, email, password_hash, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(
        query,
        (office_id, department_id, counter_id, name, username, mobile, email, password_hash, status),
        commit=True,
    )


def update_staff(
    staff_id,
    office_id,
    department_id,
    name,
    mobile,
    email,
    counter_id,
    status,
    raw_password=None,
):
    if raw_password:
        password_hash = hash_password(raw_password)
        query = """
            UPDATE staff
            SET office_id = %s, department_id = %s, counter_id = %s,
                name = %s, mobile = %s, email = %s, password_hash = %s, status = %s
            WHERE id = %s
        """
        params = (
            office_id, department_id, counter_id,
            name, mobile, email, password_hash, status, staff_id,
        )
    else:
        query = """
            UPDATE staff
            SET office_id = %s, department_id = %s, counter_id = %s,
                name = %s, mobile = %s, email = %s, status = %s
            WHERE id = %s
        """
        params = (
            office_id, department_id, counter_id,
            name, mobile, email, status, staff_id,
        )

    return execute_query(query, params, commit=True)


def get_staff_by_id(staff_id):
    query = """
        SELECT st.*,
               o.office_name,
               d.department_name,
               c.counter_number
        FROM staff st
        JOIN offices o ON st.office_id = o.id
        JOIN departments d ON st.department_id = d.id
        LEFT JOIN counters c ON st.counter_id = c.id
        WHERE st.id = %s
    """
    return execute_query(query, (staff_id,), fetch_one=True)


def get_staff_assignment_details(staff_id):
    """Fetch linked office_name, department_name, and counter_number for the staff member."""
    return get_staff_by_id(staff_id)


def get_staff_by_email(email):
    query = "SELECT * FROM staff WHERE email = %s"
    return execute_query(query, (email,), fetch_one=True)


def get_staff_by_username(username):
    if not username:
        return None
    query = "SELECT * FROM staff WHERE username = %s"
    return execute_query(query, (username,), fetch_one=True)


def get_staff_by_mobile(mobile):
    if not mobile:
        return None
    query = "SELECT * FROM staff WHERE mobile = %s"
    return execute_query(query, (mobile,), fetch_one=True)


def get_staff_by_identifier(identifier):
    if not identifier:
        return None
    query = "SELECT * FROM staff WHERE email = %s OR username = %s LIMIT 1"
    return execute_query(query, (identifier, identifier), fetch_one=True)


def get_staff_by_counter(counter_id, status="active"):
    query = """
        SELECT * FROM staff
        WHERE counter_id = %s AND status = %s
        LIMIT 1
    """
    return execute_query(query, (counter_id, status), fetch_one=True)


def list_staff_by_department(department_id, status="active"):
    query = """
        SELECT st.*, c.counter_number
        FROM staff st
        LEFT JOIN counters c ON st.counter_id = c.id
        WHERE st.department_id = %s AND st.status = %s
        ORDER BY st.name
    """
    return execute_query(query, (department_id, status), fetch_all=True) or []


def list_staff_by_office(office_id, status=None):
    if status:
        query = """
            SELECT st.*, d.department_name, c.counter_number
            FROM staff st
            JOIN departments d ON st.department_id = d.id
            LEFT JOIN counters c ON st.counter_id = c.id
            WHERE st.office_id = %s AND st.status = %s
            ORDER BY st.name
        """
        return execute_query(query, (office_id, status), fetch_all=True)

    query = """
        SELECT st.*, d.department_name, c.counter_number
        FROM staff st
        JOIN departments d ON st.department_id = d.id
        LEFT JOIN counters c ON st.counter_id = c.id
        WHERE st.office_id = %s
        ORDER BY st.name
    """
    return execute_query(query, (office_id,), fetch_all=True)


def assign_counter(staff_id, counter_id):
    query = "UPDATE staff SET counter_id = %s WHERE id = %s"
    return execute_query(query, (counter_id, staff_id), commit=True)


def update_staff_status(staff_id, status):
    query = "UPDATE staff SET status = %s WHERE id = %s"
    return execute_query(query, (status, staff_id), commit=True)


def toggle_staff_status(staff_id):
    query = """
        UPDATE staff
        SET status = IF(status = 'active', 'inactive', 'active')
        WHERE id = %s
    """
    return execute_query(query, (staff_id,), commit=True)
