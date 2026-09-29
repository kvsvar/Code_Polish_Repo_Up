"""
database.py
-----------
Handles the SQLite connection and creates all tables programmatically.
No table is ever created manually (e.g. via DB Browser) - init_db()
is called once when the app starts, and it's safe to call repeatedly
because every CREATE TABLE uses IF NOT EXISTS.
"""

import sqlite3
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash

DB_NAME = "trekking.db"


def get_db():
    """Return a new connection with rows accessible by column name."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints (SQLite disables this by default)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ---- USERS TABLE ----
    # Holds Admin, Staff, and Trekker accounts all in one table,
    # distinguished by the `role` column. This keeps auth logic simple:
    # one login form, one session mechanism, role checked afterwards.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'trekker')),
            contact TEXT,
            -- staff-only fields:
            staff_status TEXT DEFAULT NULL
                CHECK(staff_status IN ('pending', 'approved', 'blacklisted') OR staff_status IS NULL),
            -- trekker-only field:
            is_blacklisted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---- TREKS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS treks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK(difficulty IN ('Easy', 'Moderate', 'Hard')),
            duration_days INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            total_slots INTEGER NOT NULL,
            assigned_staff_id INTEGER,
            status TEXT NOT NULL DEFAULT 'Pending'
                CHECK(status IN ('Pending', 'Open','Started', 'Closed', 'Completed')),
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_staff_id) REFERENCES users(id)
        )
    """)

    # ---- BOOKINGS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trek_id INTEGER NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'Booked'
                CHECK(status IN ('Booked', 'Cancelled', 'Completed')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (trek_id) REFERENCES treks(id)
        )
    """)

    conn.commit()

    # ---- SEED ADMIN ----
    # The problem statement requires the admin to pre-exist; there is
    # no admin self-registration route.
    admin = cur.execute("SELECT id FROM users WHERE role = 'admin'").fetchone()
    if admin is None:
        cur.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@trek.com", generate_password_hash("admin123"), "admin"),
        )
        conn.commit()
        print("Seeded default admin -> email: admin@trek.com | password: admin123")

    conn.close()
