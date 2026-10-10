# 🏛️ QueueLess Government Office

> **"Skip the Line. Track Your Time. Get Served Smarter."**

An enterprise-grade, full-stack digital queue and appointment management system designed for transparent, friction-free citizen services at government offices and civic centers.

---

## 🌟 Key Features

- **📱 Citizen Self-Service Portal**:
  - Live Digital Token Generation with real-time wait estimation and queue position tracking.
  - Multi-office and service appointment booking with dynamic slot availability.
  - Historical token receipts and token status tracking.
  - Post-service Feedback & 5-Star Rating submission.
  - Real-time Smart Notification alerts when your turn is near (2 people ahead) or called.

- **🖥️ Staff Counter Management**:
  - Purpose-built counter operator desk for calling, serving, completing, or skipping tokens.
  - Automatic next-in-line token calling with sound and visual indicator support.
  - Department and counter-scoped security boundaries.

- **📊 Administrator Oversight & Analytics**:
  - Interactive Chart.js operational dashboards (Tokens per Day, Service Usage, Department Queues, Status Breakdown).
  - Multi-criteria Operational Reports with Date Range, Office, Department, and Status filtering.
  - One-click CSV Export and Print-ready audit reports.
  - Office, Department, Service, Counter, and Staff lifecycle management.

- **🔒 Enterprise Security & Protection**:
  - Centralized input sanitization against XSS attacks.
  - 100% parameterized SQL queries via PyMySQL preventing SQL Injection.
  - Strict role-based authorization with custom HTTP 403, 404, and 500 error pages.
  - Secure session cookies (`HttpOnly`, `SameSite=Lax`, 8-hour lifetime).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.10+ • Flask • Werkzeug |
| **Database** | MySQL (XAMPP / MariaDB) • PyMySQL (DictCursor) |
| **Frontend UI** | HTML5 • CSS3 (Government Digital Service Theme) • JavaScript (ES6) |
| **UI Frameworks** | Bootstrap 5.3.3 • Bootstrap Icons • Font Awesome 6 |
| **Data Visualizations** | Chart.js 4.4 |
| **Security** | Werkzeug Security (Scrypt / PBKDF2), Custom Regex Validators |

---

## 📋 Prerequisites

Before installing the project, ensure you have:
1. **Python 3.10 or higher** installed ([python.org](https://www.python.org/downloads/)).
2. **XAMPP** (or MySQL Server) with Apache & MySQL running.
3. Git (optional, for version control).

---

## 🚀 Quick Start & Installation

### 1. Clone or Open the Project
```bash
cd d:/hackathon/QueueLess
```

### 2. Set Up Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup (MySQL / XAMPP)
1. Open **XAMPP Control Panel** and start **Apache** and **MySQL**.
2. Open **phpMyAdmin** (`http://localhost/phpmyadmin`) or MySQL Command Line.
3. Create the database:
   ```sql
   CREATE DATABASE queueless_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
4. Import the database schema:
   - In phpMyAdmin: Select `queueless_db` -> Click **Import** -> Choose `database/schema.sql` -> Click **Go**.
   - Or via MySQL CLI:
     ```bash
     mysql -u root -p queueless_db < database/schema.sql
     ```

### 5. Environment Configuration (Optional)
A `.env` file can be placed in the project root:
```env
SECRET_KEY=your-secure-secret-key-change-in-production
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=queueless_db
DB_PORT=3306
```

### 6. Seed Complete Demo Data (For Project Demonstrations)
Run the automated demonstration data seeder to immediately populate sample offices, counters, staff, active tokens, appointments, and feedback:
```bash
python utils/seed_demo_data.py
```

### 7. Run the Application
```bash
python app.py
```
Visit **[http://localhost:5000](http://localhost:5000)** in your web browser!

---

## 🔑 Default Login Credentials

Use the following pre-configured accounts for demonstration and evaluation:

| Role | Email | Password | Access Area |
|---|---|---|---|
| **Administrator** | `admin@queueless.gov` | `admin123` | `/admin` (Full System Overview & Analytics) |
| **Staff Member** | `staff@queueless.gov` | `staff123` | `/staff` (Counter A1 Operations) |
| **Demo Citizen** | `citizen@queueless.gov` | `citizen123` | `/citizen` (Tokens, Appointments & Tracking) |

---

## 🎬 Project Demonstration Workflow Guide

Follow these steps for a complete live showcase:

1. **Step 1: Admin Configuration & Analytics**
   - Log in as Admin (`admin@queueless.gov` / `admin123`).
   - Observe the **Analytics Dashboard** featuring real-time Chart.js visual graphs (Daily Tokens, Service Distribution, Department Queues, Status Breakdown).
   - Navigate to **Reports & Analytics** (`/admin/reports`) to test live filtering and click **Export to CSV**.

2. **Step 2: Staff Counter Desk**
   - Open an incognito/private browser window and log in as Staff (`staff@queueless.gov` / `staff123`).
   - View the active Counter A1 queue with serving and waiting tokens.

3. **Step 3: Citizen Experience**
   - In a standard browser window, log in as Citizen (`citizen@queueless.gov` / `citizen123`).
   - Click **Get Token** -> Select Office, Department, and Service -> Generate Token.
   - Watch the **Live Queue Tracking** screen update dynamically every 5 seconds.
   - Click **Book Appt** to schedule a timed appointment slot.

4. **Step 4: Queue Execution & Turn Notification**
   - On the Staff screen, click **Call Next Token** or **Start Serving**.
   - On the Citizen screen, notice the dynamic popup modal alert: *"It's your turn! Please proceed to Counter A1."*
   - Staff clicks **Complete Token**.

5. **Step 5: Citizen Feedback & Rating**
   - On the Citizen screen, navigate to **History** -> Click **Give Feedback** next to the completed token.
   - Submit a 5-star rating with comments.
   - Switch back to Admin -> **Feedback & Reviews** to view the live rating update!

---

## 📁 Project Directory Structure

```
QueueLess/
├── app.py                      # Flask Application entry point & error handlers
├── config.py                   # Environment & Session Security Configurations
├── requirements.txt            # Python Package Dependencies
├── README.md                   # Project Documentation
│
├── database/
│   └── schema.sql              # MySQL Database Relational Schema
│
├── models/                     # Data Access Layer & Business Logic
│   ├── admin.py                # Admin metrics and analytics queries
│   ├── appointment.py          # Appointment booking & slot availability
│   ├── counter.py              # Counter desk management
│   ├── department.py           # Department records
│   ├── feedback.py             # Citizen feedback & ratings
│   ├── notifications.py        # Real-time alert notifications
│   ├── office.py               # Government offices directory
│   ├── service.py              # Public services catalog
│   ├── staff.py                # Staff accounts & counter assignments
│   ├── token.py                # Queue tokens & state machine
│   └── user.py                 # Citizen profiles & authentication
│
├── routes/                     # Blueprint Route Controllers
│   ├── admin_routes.py         # Administrative endpoints & CSV export
│   ├── api_routes.py           # JSON REST APIs for slots & live polling
│   ├── auth_routes.py          # Authentication (Login, Register, Logout)
│   ├── citizen_routes.py       # Citizen queue, appointment & feedback
│   ├── queue_routes.py         # Public queue display
│   └── staff_routes.py         # Staff counter operations
│
├── static/
│   ├── css/
│   │   ├── admin.css           # Admin layout styles
│   │   └── style.css           # Government Digital Service Theme (Custom CSS)
│   └── js/
│       └── main.js             # Client interactive engine & alert toasts
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Master Layout with Google Fonts & responsive navbar
│   ├── index.html              # Landing Homepage
│   ├── admin/                  # Admin portal views & Chart.js dashboard
│   ├── auth/                   # Login & Registration views
│   ├── citizen/                # Citizen portal views (Live Queue, Feedback)
│   ├── errors/                 # Custom HTTP 400, 403, 404, 500 error pages
│   └── staff/                  # Staff counter dashboard views
│
└── utils/                      # Helper Utilities & Security Tools
    ├── auth.py                 # Password hashing & role-based decorators
    ├── db.py                   # PyMySQL connection pool & query executor
    ├── seed_demo_data.py       # Demonstration data seeder script
    └── validators.py           # XSS sanitization, email, mobile & date validation
```

---

## 📜 License & Acknowledgments

Developed for the **QueueLess Government Office** project. Built to modernize public administration through transparency, digital queuing, and automated citizen engagement.
