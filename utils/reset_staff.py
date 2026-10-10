"""Create or update a default QueueLess staff account with a Werkzeug/auth password hash."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.auth import hash_password, verify_password
from utils.db import execute_query

STAFF_NAME = "Rajesh Kumar"
STAFF_EMAIL = "staff@queueless.gov"
STAFF_PASSWORD = "staff123"
STAFF_MOBILE = "9876543210"
OFFICE_ID = 1
DEPARTMENT_ID = 1
COUNTER_ID = 1


def upsert_staff():
    password_hash = hash_password(STAFF_PASSWORD)

    existing = execute_query(
        "SELECT id FROM staff WHERE email = %s",
        (STAFF_EMAIL,),
        fetch_one=True,
    )

    if existing:
        execute_query(
            """
            UPDATE staff
            SET office_id = %s, department_id = %s, counter_id = %s,
                name = %s, mobile = %s, password_hash = %s, status = 'active'
            WHERE email = %s
            """,
            (
                OFFICE_ID,
                DEPARTMENT_ID,
                COUNTER_ID,
                STAFF_NAME,
                STAFF_MOBILE,
                password_hash,
                STAFF_EMAIL,
            ),
            commit=True,
        )
        action = "updated"
    else:
        execute_query(
            """
            INSERT INTO staff
                (office_id, department_id, counter_id, name, mobile, email, password_hash, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
            """,
            (
                OFFICE_ID,
                DEPARTMENT_ID,
                COUNTER_ID,
                STAFF_NAME,
                STAFF_MOBILE,
                STAFF_EMAIL,
                password_hash,
            ),
            commit=True,
        )
        action = "created"

    row = execute_query(
        "SELECT email, password_hash, status FROM staff WHERE email = %s",
        (STAFF_EMAIL,),
        fetch_one=True,
    )
    verified = bool(row) and verify_password(STAFF_PASSWORD, row["password_hash"])

    print(f"Staff account {action} successfully!")
    print(f"Email: {STAFF_EMAIL}")
    print(f"Password: {STAFF_PASSWORD}")
    print(f"Status: {row['status'] if row else 'missing'}")
    print(f"Password hash verified: {verified}")

    if not verified:
        raise SystemExit("Staff password hash could not be verified.")


if __name__ == "__main__":
    upsert_staff()
