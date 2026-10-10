"""Appointment data access methods."""

from utils.db import execute_query
from datetime import datetime, timedelta

def create_appointment(user_id, office_id, department_id, service_id, appointment_date, appointment_time):
    # Parse appointment_time from "%I:%M %p" (e.g., "09:00 AM") to "%H:%M:%S"
    try:
        if "AM" in appointment_time or "PM" in appointment_time:
            parsed_time = datetime.strptime(appointment_time, "%I:%M %p")
            appointment_time = parsed_time.strftime("%H:%M:%S")
    except ValueError:
        pass  # Fallback if it's already in the correct format or invalid

    # 1. Check daily limit
    service_query = "SELECT daily_limit FROM services WHERE id = %s"
    service = execute_query(service_query, (service_id,), fetch_one=True)
    if not service:
        return False, "Service not found."
    
    daily_limit = service['daily_limit']
    
    # Get current bookings for the day
    count_query = """
        SELECT COUNT(*) as count 
        FROM appointments 
        WHERE service_id = %s AND appointment_date = %s 
        AND status NOT IN ('cancelled', 'no_show')
    """
    booked_result = execute_query(count_query, (service_id, appointment_date), fetch_one=True)
    booked_count = booked_result['count'] if booked_result else 0
    
    if booked_count >= daily_limit:
        return False, "Daily limit reached for this service."
        
    # 2. Check slot capacity (prevent double booking the exact time slot for the same service)
    slot_query = """
        SELECT COUNT(*) as count 
        FROM appointments 
        WHERE service_id = %s AND appointment_date = %s AND appointment_time = %s
        AND status NOT IN ('cancelled', 'no_show')
    """
    slot_result = execute_query(slot_query, (service_id, appointment_date, appointment_time), fetch_one=True)
    slot_count = slot_result['count'] if slot_result else 0
    
    # We will assume 1 appointment per exact time slot per service for simplicity unless counters are specified
    if slot_count > 0:
        return False, "This time slot is already booked."

    # 3. Insert new appointment
    insert_query = """
        INSERT INTO appointments
            (user_id, office_id, department_id, service_id, appointment_date, appointment_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
    """
    success = execute_query(
        insert_query,
        (user_id, office_id, department_id, service_id, appointment_date, appointment_time),
        commit=True
    )
    
    if success:
        return True, "Appointment booked successfully."
    return False, "Failed to book appointment."


def get_user_appointments(user_id):
    query = """
        SELECT a.*, o.office_name, d.department_name, s.service_name
        FROM appointments a
        JOIN offices o ON a.office_id = o.id
        JOIN departments d ON a.department_id = d.id
        JOIN services s ON a.service_id = s.id
        WHERE a.user_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """
    return execute_query(query, (user_id,), fetch_all=True) or []


def get_available_slots(service_id, appointment_date):
    # 1. Get service and office details
    query = """
        SELECT s.daily_limit, s.average_time, o.opening_time, o.closing_time
        FROM services s
        JOIN departments d ON s.department_id = d.id
        JOIN offices o ON d.office_id = o.id
        WHERE s.id = %s
    """
    details = execute_query(query, (service_id,), fetch_one=True)
    if not details:
        return []
        
    daily_limit = details['daily_limit']
    average_time = details['average_time'] # in minutes
    
    # Check total bookings for the day
    count_query = """
        SELECT COUNT(*) as count 
        FROM appointments 
        WHERE service_id = %s AND appointment_date = %s 
        AND status NOT IN ('cancelled', 'no_show')
    """
    booked_result = execute_query(count_query, (service_id, appointment_date), fetch_one=True)
    booked_count = booked_result['count'] if booked_result else 0
    
    if booked_count >= daily_limit:
        return [] # Daily capacity full
        
    # 2. Get already booked times
    booked_times_query = """
        SELECT appointment_time
        FROM appointments
        WHERE service_id = %s AND appointment_date = %s
        AND status NOT IN ('cancelled', 'no_show')
    """
    booked_times_raw = execute_query(booked_times_query, (service_id, appointment_date), fetch_all=True) or []
    # MySQL TIMEDELTA might be returned as timedelta objects. We need string HH:MM:00
    booked_times = []
    for row in booked_times_raw:
        if isinstance(row['appointment_time'], timedelta):
            # Convert timedelta to string HH:MM:SS
            total_seconds = int(row['appointment_time'].total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            booked_times.append(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            booked_times.append(str(row['appointment_time']))
            
    # 3. Generate slots
    slots = []
    # Assuming opening_time and closing_time are timedelta or strings
    def to_datetime(t):
        if isinstance(t, timedelta):
            total_seconds = int(t.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", "%H:%M:%S")
        return datetime.strptime(str(t), "%H:%M:%S")

    current_time = to_datetime(details['opening_time'])
    end_time = to_datetime(details['closing_time'])
    
    while current_time + timedelta(minutes=average_time) <= end_time:
        time_str = current_time.strftime("%H:%M:%S")
        if time_str not in booked_times:
            slots.append(current_time.strftime("%I:%M %p"))
        current_time += timedelta(minutes=average_time)
        
    return slots


def cancel_appointment(appointment_id, user_id):
    query = """
        UPDATE appointments 
        SET status = 'cancelled' 
        WHERE id = %s AND user_id = %s AND status = 'scheduled'
    """
    return execute_query(query, (appointment_id, user_id), commit=True)


def get_all_appointments_admin():
    query = """
        SELECT a.*, u.full_name as citizen_name, u.mobile, o.office_name, d.department_name, s.service_name
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN offices o ON a.office_id = o.id
        JOIN departments d ON a.department_id = d.id
        JOIN services s ON a.service_id = s.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """
    return execute_query(query, fetch_all=True) or []


def get_todays_appointments_staff(office_id, department_id):
    today = datetime.now().date()
    query = """
        SELECT a.*, u.full_name as citizen_name, u.mobile, s.service_name
        FROM appointments a
        JOIN users u ON a.user_id = u.id
        JOIN services s ON a.service_id = s.id
        WHERE a.office_id = %s AND a.department_id = %s AND a.appointment_date = %s
        ORDER BY a.appointment_time ASC
    """
    return execute_query(query, (office_id, department_id, today), fetch_all=True) or []
