"""
Seed script to populate queueless_db with rich demonstration data.
Ideal for final academic and college project evaluations.
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from werkzeug.security import generate_password_hash
from utils.db import execute_query


def run_seed():
    print("==================================================")
    print("   QueueLess Demo Data Seeder - Starting...      ")
    print("==================================================")

    # 1. Ensure Default Admin Account
    admin_email = "admin@queueless.gov"
    admin_pwd_hash = generate_password_hash("admin123")
    existing_admin = execute_query("SELECT id FROM admins WHERE email = %s", (admin_email,), fetch_one=True)
    if existing_admin:
        execute_query(
            "UPDATE admins SET name = 'System Administrator', username = 'admin', password_hash = %s, status = 'active' WHERE email = %s",
            (admin_pwd_hash, admin_email),
            commit=True,
        )
        print("[OK] Admin verified: admin@queueless.gov / admin123")
    else:
        execute_query(
            "INSERT INTO admins (name, username, email, password_hash, status) VALUES ('System Administrator', 'admin', %s, %s, 'active')",
            (admin_email, admin_pwd_hash),
            commit=True,
        )
        print("[OK] Admin created: admin@queueless.gov / admin123")

    # 2. Seed Offices
    offices_data = [
        ("Rajkot Mamlatdar Office", "Karanpara, Near ST Bus Stand", "Rajkot", "0281-2234567", "09:00:00", "18:00:00"),
        ("District Collectorate Ahmedabad", "Subhash Bridge, Ashram Road", "Ahmedabad", "079-27551234", "09:30:00", "17:30:00"),
        ("Surat Municipal Civic Center", "Muglisara, Main Road", "Surat", "0261-2423751", "10:00:00", "17:00:00"),
    ]
    for o_name, addr, city, phone, op_time, cl_time in offices_data:
        exists = execute_query("SELECT id FROM offices WHERE office_name = %s", (o_name,), fetch_one=True)
        if not exists:
            execute_query(
                "INSERT INTO offices (office_name, address, city, phone, opening_time, closing_time, status) VALUES (%s, %s, %s, %s, %s, %s, 'active')",
                (o_name, addr, city, phone, op_time, cl_time),
                commit=True,
            )
    print("[OK] Government Offices seeded.")

    # Fetch main office id
    main_office = execute_query("SELECT id FROM offices WHERE office_name LIKE %s LIMIT 1", ("%Rajkot%",), fetch_one=True)
    office_id = main_office["id"] if main_office else 1

    # 3. Seed Departments
    depts_data = [
        ("Citizen Services", "General citizen certificates and grievance handling"),
        ("Revenue & Land Records", "Land registration, mutation, and records verification"),
        ("Identity & Verification", "Aadhaar, income, and domicile verification"),
    ]
    for d_name, desc in depts_data:
        exists = execute_query("SELECT id FROM departments WHERE office_id = %s AND department_name = %s", (office_id, d_name), fetch_one=True)
        if not exists:
            execute_query(
                "INSERT INTO departments (office_id, department_name, description, status) VALUES (%s, %s, %s, 'active')",
                (office_id, d_name, desc),
                commit=True,
            )
    print("[OK] Departments seeded.")

    dept_1 = execute_query("SELECT id FROM departments WHERE office_id = %s AND department_name = 'Citizen Services'", (office_id,), fetch_one=True)
    dept_1_id = dept_1["id"] if dept_1 else 1

    dept_2 = execute_query("SELECT id FROM departments WHERE office_id = %s AND department_name = 'Revenue & Land Records'", (office_id,), fetch_one=True)
    dept_2_id = dept_2["id"] if dept_2 else 2

    # 4. Seed Services
    services_data = [
        (dept_1_id, "Income Certificate", "Issue official income certificates", 6, 100),
        (dept_1_id, "Caste Certificate", "Verification and issuance of caste certificates", 8, 80),
        (dept_1_id, "Residence Certificate", "Proof of state residence certificate", 5, 120),
        (dept_2_id, "Land Mutation (7/12)", "Transfer of agricultural land ownership", 10, 60),
    ]
    for d_id, s_name, desc, avg_t, d_limit in services_data:
        exists = execute_query("SELECT id FROM services WHERE department_id = %s AND service_name = %s", (d_id, s_name), fetch_one=True)
        if not exists:
            execute_query(
                "INSERT INTO services (department_id, service_name, description, average_time, daily_limit, status) VALUES (%s, %s, %s, %s, %s, 'active')",
                (d_id, s_name, desc, avg_t, d_limit),
                commit=True,
            )
    print("[OK] Services with operational metrics seeded.")

    service_1 = execute_query("SELECT id FROM services WHERE service_name = 'Income Certificate'", fetch_one=True)
    service_id = service_1["id"] if service_1 else 1

    # 5. Seed Counters
    counters_data = [("A1", dept_1_id), ("A2", dept_1_id), ("B1", dept_2_id)]
    for c_num, d_id in counters_data:
        exists = execute_query("SELECT id FROM counters WHERE office_id = %s AND department_id = %s AND counter_number = %s", (office_id, d_id, c_num), fetch_one=True)
        if not exists:
            execute_query(
                "INSERT INTO counters (office_id, department_id, counter_number, status) VALUES (%s, %s, %s, 'active')",
                (office_id, d_id, c_num),
                commit=True,
            )
    print("[OK] Counter desks seeded.")

    counter_1 = execute_query("SELECT id FROM counters WHERE office_id = %s AND counter_number = 'A1'", (office_id,), fetch_one=True)
    counter_id = counter_1["id"] if counter_1 else 1

    # 6. Seed Staff Accounts
    staff_pwd_hash = generate_password_hash("staff123")
    staff_email = "staff@queueless.gov"
    existing_staff = execute_query("SELECT id FROM staff WHERE email = %s", (staff_email,), fetch_one=True)
    if existing_staff:
        execute_query(
            "UPDATE staff SET name = 'Rajesh Sharma', username = 'staff', password_hash = %s, office_id = %s, department_id = %s, counter_id = %s, status = 'active' WHERE email = %s",
            (staff_pwd_hash, office_id, dept_1_id, counter_id, staff_email),
            commit=True,
        )
        print("[OK] Staff verified: staff@queueless.gov / staff123 (Counter A1)")
    else:
        execute_query(
            "INSERT INTO staff (office_id, department_id, counter_id, name, username, mobile, email, password_hash, status) VALUES (%s, %s, %s, 'Rajesh Sharma', 'staff', '9876543210', %s, %s, 'active')",
            (office_id, dept_1_id, counter_id, staff_email, staff_pwd_hash),
            commit=True,
        )
        print("[OK] Staff created: staff@queueless.gov / staff123 (Counter A1)")

    # 7. Seed Citizens
    citizen_pwd_hash = generate_password_hash("citizen123")
    citizen_email = "citizen@queueless.gov"
    existing_citizen = execute_query("SELECT id FROM users WHERE email = %s", (citizen_email,), fetch_one=True)
    if existing_citizen:
        citizen_id = existing_citizen["id"]
        execute_query("UPDATE users SET password_hash = %s, status = 'active' WHERE id = %s", (citizen_pwd_hash, citizen_id), commit=True)
        print("[OK] Demo Citizen verified: citizen@queueless.gov / citizen123")
    else:
        citizen_id = execute_query(
            "INSERT INTO users (full_name, mobile, email, password_hash, address, status) VALUES ('Amit Kumar', '9825012345', %s, %s, '12 Royal Park, Rajkot', 'active')",
            (citizen_email, citizen_pwd_hash),
            commit=True,
        )
        print("[OK] Demo Citizen created: citizen@queueless.gov / citizen123")

    # 8. Seed Historical Tokens (Past 6 days for rich Chart.js visuals)
    today = date.today()
    for days_ago in range(6, 0, -1):
        token_day = today - timedelta(days=days_ago)
        count_for_day = 8 + (days_ago * 2)
        for i in range(1, count_for_day + 1):
            t_num = f"A-{i:03d}"
            # Check if token exists
            t_exists = execute_query("SELECT id FROM tokens WHERE department_id = %s AND token_date = %s AND token_number = %s", (dept_1_id, token_day, t_num), fetch_one=True)
            if not t_exists:
                execute_query(
                    """
                    INSERT INTO tokens (token_number, user_id, office_id, department_id, service_id, counter_id, token_date, status, created_at, called_at, serving_at, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'completed', %s, %s, %s, %s)
                    """,
                    (
                        t_num, citizen_id, office_id, dept_1_id, service_id, counter_id, token_day,
                        datetime.combine(token_day, datetime.min.time().replace(hour=9, minute=15)),
                        datetime.combine(token_day, datetime.min.time().replace(hour=9, minute=30)),
                        datetime.combine(token_day, datetime.min.time().replace(hour=9, minute=32)),
                        datetime.combine(token_day, datetime.min.time().replace(hour=9, minute=45)),
                    ),
                    commit=True,
                )

    # 9. Seed Active Tokens for Today
    today_tokens = [
        ("A-001", "completed", 9, 10, 9, 25),
        ("A-002", "serving", 9, 30, None, None),
        ("A-003", "waiting", None, None, None, None),
        ("A-004", "waiting", None, None, None, None),
    ]
    for t_num, status, c_h, c_m, comp_h, comp_m in today_tokens:
        t_exists = execute_query("SELECT id FROM tokens WHERE department_id = %s AND token_date = %s AND token_number = %s", (dept_1_id, today, t_num), fetch_one=True)
        if not t_exists:
            called_time = datetime.combine(today, datetime.min.time().replace(hour=c_h, minute=c_m)) if c_h else None
            completed_time = datetime.combine(today, datetime.min.time().replace(hour=comp_h, minute=comp_m)) if comp_h else None
            execute_query(
                """
                INSERT INTO tokens (token_number, user_id, office_id, department_id, service_id, counter_id, token_date, status, called_at, serving_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (t_num, citizen_id, office_id, dept_1_id, service_id, counter_id, today, status, called_time, called_time, completed_time),
                commit=True,
            )

    print("[OK] Daily tokens and active queue tokens seeded.")

    # 10. Seed Demo Feedback
    completed_token = execute_query("SELECT id FROM tokens WHERE status = 'completed' LIMIT 1", fetch_one=True)
    if completed_token:
        fb_exists = execute_query("SELECT id FROM feedback WHERE token_id = %s", (completed_token["id"],), fetch_one=True)
        if not fb_exists:
            execute_query(
                "INSERT INTO feedback (user_id, token_id, rating, comment) VALUES (%s, %s, 5, 'Quick service at Counter A1! I got my certificate in under 10 minutes.')",
                (citizen_id, completed_token["id"]),
                commit=True,
            )
            print("[OK] Demonstration citizen feedback recorded.")

    # 11. Seed Future Appointments
    appt_date = today + timedelta(days=2)
    appt_exists = execute_query("SELECT id FROM appointments WHERE user_id = %s AND appointment_date = %s", (citizen_id, appt_date), fetch_one=True)
    if not appt_exists:
        execute_query(
            """
            INSERT INTO appointments (user_id, office_id, department_id, service_id, appointment_date, appointment_time, status)
            VALUES (%s, %s, %s, %s, %s, '10:30:00', 'scheduled')
            """,
            (citizen_id, office_id, dept_1_id, service_id, appt_date),
            commit=True,
        )
        print("[OK] Scheduled demonstration appointment seeded.")

    # 12. Seed Notifications
    notif_exists = execute_query("SELECT id FROM notifications WHERE user_id = %s LIMIT 1", (citizen_id,), fetch_one=True)
    if not notif_exists:
        execute_query(
            """
            INSERT INTO notifications (user_id, title, message, type, is_read)
            VALUES (%s, 'Welcome to QueueLess!', 'You can now book appointments and get digital queue tokens from anywhere.', 'info', 0),
                   (%s, 'Token Notice', 'Your token A-002 is currently serving at Counter A1.', 'token_update', 0)
            """,
            (citizen_id, citizen_id),
            commit=True,
        )
        print("[OK] Smart notifications seeded.")

    print("==================================================")
    print("   [OK] Demo Data Seeding Completed Successfully!    ")
    print("==================================================")
    print("Default Logins:")
    print("  • Admin:   admin@queueless.gov   / admin123")
    print("  • Staff:   staff@queueless.gov   / staff123")
    print("  • Citizen: citizen@queueless.gov / citizen123")
    print("==================================================")


if __name__ == "__main__":
    run_seed()
