"""Create or update the default QueueLess administrator with a Werkzeug password hash."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.security import check_password_hash, generate_password_hash

from utils.db import execute_query

ADMIN_NAME = "System Administrator"
ADMIN_EMAIL = "admin@queueless.gov"
ADMIN_PASSWORD = "admin123"


def upsert_admin():
    password_hash = generate_password_hash(ADMIN_PASSWORD)

    existing = execute_query(
        "SELECT id FROM admins WHERE email = %s",
        (ADMIN_EMAIL,),
        fetch_one=True,
    )

    if existing:
        execute_query(
            """
            UPDATE admins
            SET name = %s, password_hash = %s, status = 'active'
            WHERE email = %s
            """,
            (ADMIN_NAME, password_hash, ADMIN_EMAIL),
            commit=True,
        )
        action = "updated"
    else:
        execute_query(
            """
            INSERT INTO admins (name, email, password_hash, status)
            VALUES (%s, %s, %s, 'active')
            """,
            (ADMIN_NAME, ADMIN_EMAIL, password_hash),
            commit=True,
        )
        action = "created"

    row = execute_query(
        "SELECT email, password_hash, status FROM admins WHERE email = %s",
        (ADMIN_EMAIL,),
        fetch_one=True,
    )
    verified = bool(row) and check_password_hash(row["password_hash"], ADMIN_PASSWORD)

    print(f"Admin {action}: {ADMIN_EMAIL}")
    print(f"Status: {row['status'] if row else 'missing'}")
    print(f"Password hash verified: {verified}")
    if not verified:
        raise SystemExit("Admin password hash could not be verified.")


if __name__ == "__main__":
    upsert_admin()
