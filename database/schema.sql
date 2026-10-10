-- QueueLess Government Office - Full Database Schema
-- Run in phpMyAdmin or MySQL CLI (XAMPP)

CREATE DATABASE IF NOT EXISTS queueless_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE queueless_db;

-- Drop existing tables (child tables first)
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS tokens;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS counters;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS offices;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;

-- ---------------------------------------------------------------------------
-- 1. users
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(150)  NOT NULL,
    mobile        VARCHAR(15)   NOT NULL,
    email         VARCHAR(150)  NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    address       TEXT,
    status        ENUM('active', 'inactive', 'blocked') NOT NULL DEFAULT 'active',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_users_mobile (mobile),
    UNIQUE KEY uq_users_email (email),
    INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 2. admins
-- ---------------------------------------------------------------------------
CREATE TABLE admins (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    username      VARCHAR(100) NULL,
    email         VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status        ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_admins_email (email),
    UNIQUE KEY uq_admins_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 3. offices
-- ---------------------------------------------------------------------------
CREATE TABLE offices (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    office_name   VARCHAR(200) NOT NULL,
    address       TEXT         NOT NULL,
    city          VARCHAR(100) NOT NULL,
    phone         VARCHAR(20),
    opening_time  TIME         NOT NULL DEFAULT '09:00:00',
    closing_time  TIME         NOT NULL DEFAULT '17:00:00',
    status        ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_offices_city (city),
    INDEX idx_offices_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 4. departments
-- ---------------------------------------------------------------------------
CREATE TABLE departments (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    office_id       INT UNSIGNED NOT NULL,
    department_name VARCHAR(150) NOT NULL,
    description     TEXT,
    status          ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_departments_office
        FOREIGN KEY (office_id) REFERENCES offices(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_departments_office (office_id),
    INDEX idx_departments_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 5. services
-- ---------------------------------------------------------------------------
CREATE TABLE services (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    department_id   INT UNSIGNED NOT NULL,
    service_name    VARCHAR(150) NOT NULL,
    description     TEXT,
    average_time    INT UNSIGNED NOT NULL DEFAULT 15 COMMENT 'Average service time in minutes',
    daily_limit     INT UNSIGNED NOT NULL DEFAULT 100,
    status          ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_services_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_services_department (department_id),
    INDEX idx_services_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 6. counters
-- ---------------------------------------------------------------------------
CREATE TABLE counters (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    office_id       INT UNSIGNED NOT NULL,
    department_id   INT UNSIGNED NOT NULL,
    counter_number  VARCHAR(20)  NOT NULL,
    status          ENUM('active', 'inactive', 'closed') NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_counters_office
        FOREIGN KEY (office_id) REFERENCES offices(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_counters_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uq_counters_office_dept_number (office_id, department_id, counter_number),
    INDEX idx_counters_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 7. staff
-- ---------------------------------------------------------------------------
CREATE TABLE staff (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    office_id       INT UNSIGNED NOT NULL,
    department_id   INT UNSIGNED NOT NULL,
    counter_id      INT UNSIGNED NULL,
    name            VARCHAR(150) NOT NULL,
    username        VARCHAR(100) NULL,
    mobile          VARCHAR(15)  NOT NULL,
    email           VARCHAR(150) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    status          ENUM('active', 'inactive', 'on_break') NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_staff_office
        FOREIGN KEY (office_id) REFERENCES offices(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_staff_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_staff_counter
        FOREIGN KEY (counter_id) REFERENCES counters(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    UNIQUE KEY uq_staff_mobile (mobile),
    UNIQUE KEY uq_staff_email (email),
    UNIQUE KEY uq_staff_username (username),
    INDEX idx_staff_office (office_id),
    INDEX idx_staff_department (department_id),
    INDEX idx_staff_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 8. tokens
-- ---------------------------------------------------------------------------
CREATE TABLE tokens (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    token_number    VARCHAR(20)  NOT NULL,
    user_id         INT UNSIGNED NOT NULL,
    office_id       INT UNSIGNED NOT NULL,
    department_id   INT UNSIGNED NOT NULL,
    service_id      INT UNSIGNED NOT NULL,
    counter_id      INT UNSIGNED NULL,
    token_date      DATE         NOT NULL,
    status          ENUM('waiting', 'called', 'serving', 'completed', 'cancelled', 'no_show')
                    NOT NULL DEFAULT 'waiting',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    called_at       TIMESTAMP NULL DEFAULT NULL,
    serving_at      TIMESTAMP NULL DEFAULT NULL,
    completed_at    TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_tokens_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tokens_office
        FOREIGN KEY (office_id) REFERENCES offices(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tokens_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tokens_service
        FOREIGN KEY (service_id) REFERENCES services(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_tokens_counter
        FOREIGN KEY (counter_id) REFERENCES counters(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_tokens_user (user_id),
    INDEX idx_tokens_office_date (office_id, token_date),
    INDEX idx_tokens_status (status),
    INDEX idx_tokens_department_date (department_id, token_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 9. appointments
-- ---------------------------------------------------------------------------
CREATE TABLE appointments (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id           INT UNSIGNED NOT NULL,
    office_id         INT UNSIGNED NOT NULL,
    department_id     INT UNSIGNED NOT NULL,
    service_id        INT UNSIGNED NOT NULL,
    appointment_date  DATE NOT NULL,
    appointment_time  TIME NOT NULL,
    status            ENUM('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')
                      NOT NULL DEFAULT 'scheduled',
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointments_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_office
        FOREIGN KEY (office_id) REFERENCES offices(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_service
        FOREIGN KEY (service_id) REFERENCES services(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_appointments_user (user_id),
    INDEX idx_appointments_office_date (office_id, appointment_date),
    INDEX idx_appointments_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 10. notifications
-- ---------------------------------------------------------------------------
CREATE TABLE notifications (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    token_id    INT UNSIGNED NULL,
    title       VARCHAR(200) NOT NULL,
    message     TEXT         NOT NULL,
    type        ENUM('info', 'warning', 'token_update', 'appointment') NOT NULL DEFAULT 'info',
    is_read     TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notifications_token
        FOREIGN KEY (token_id) REFERENCES tokens(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_notifications_user (user_id),
    INDEX idx_notifications_is_read (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 11. feedback
-- ---------------------------------------------------------------------------
CREATE TABLE feedback (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    token_id    INT UNSIGNED NOT NULL,
    rating      TINYINT UNSIGNED NOT NULL,
    comment     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_feedback_token
        FOREIGN KEY (token_id) REFERENCES tokens(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5),
    INDEX idx_feedback_user (user_id),
    INDEX idx_feedback_token (token_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===========================================================================
-- SEED DATA
-- ===========================================================================

-- Default admin (password: admin123, created/updated by: python utils/create_admin.py)
-- Login: admin@queueless.gov / admin123
INSERT INTO admins (name, email, password_hash, status) VALUES
(
    'System Administrator',
    'admin@queueless.gov',
    'scrypt:32768:8:1$9fYfq6Xsva02o7MQ$e83cce492c92fd1e5721a4fda0737cd5056053a17051fed894d5009a79063d43ec49640fd90d996433fdd432bd51c637bfad118f54ab0a229f074f30aec8aef3',
    'active'
);

-- Offices
INSERT INTO offices (office_name, address, city, phone, opening_time, closing_time, status) VALUES
('District Collector Office', 'Collectorate Building, Civil Lines', 'Ahmedabad', '079-25501234', '09:00:00', '17:00:00', 'active'),
('Municipal Corporation Office', 'MC Building, Ashram Road', 'Ahmedabad', '079-25505678', '10:00:00', '18:00:00', 'active'),
('Revenue Department Office', 'Revenue Bhavan, Sector 12', 'Gandhinagar', '079-23234567', '09:30:00', '17:30:00', 'active');

-- Departments (office_id: 1 = Collector, 2 = Municipal, 3 = Revenue)
INSERT INTO departments (office_id, department_name, description, status) VALUES
(1, 'Citizen Services', 'General citizen grievance and certificate services', 'active'),
(1, 'Land Records', 'Land registration and mutation services', 'active'),
(2, 'Property Tax', 'Property tax assessment and payment', 'active'),
(2, 'Building Permission', 'Construction and building plan approvals', 'active'),
(3, 'Income Certificate', 'Income and domicile certificate issuance', 'active'),
(3, 'Caste Certificate', 'SC/ST/OBC certificate verification and issuance', 'active');

-- Services
INSERT INTO services (department_id, service_name, description, average_time, daily_limit, status) VALUES
(1, 'Birth Certificate', 'Apply for or obtain a birth certificate', 20, 80, 'active'),
(1, 'Death Certificate', 'Apply for or obtain a death certificate', 20, 60, 'active'),
(2, 'Land Mutation', 'Transfer of land ownership records', 30, 40, 'active'),
(2, 'Encumbrance Certificate', 'Property encumbrance verification', 25, 50, 'active'),
(3, 'Property Tax Payment', 'Pay annual property tax dues', 15, 120, 'active'),
(3, 'Tax Assessment', 'Request property tax reassessment', 25, 60, 'active'),
(4, 'Building Plan Approval', 'Submit and track building plan applications', 45, 30, 'active'),
(5, 'Income Certificate', 'Apply for income certificate', 20, 70, 'active'),
(6, 'Caste Certificate', 'Apply for caste certificate', 25, 65, 'active');

-- Counters
INSERT INTO counters (office_id, department_id, counter_number, status) VALUES
(1, 1, 'A1', 'active'),
(1, 1, 'A2', 'active'),
(1, 2, 'B1', 'active'),
(2, 3, 'C1', 'active'),
(2, 3, 'C2', 'active'),
(2, 4, 'D1', 'active'),
(3, 5, 'E1', 'active'),
(3, 6, 'F1', 'active');
