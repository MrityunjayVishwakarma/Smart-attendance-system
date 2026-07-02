"""
SQLite table definitions for Smart Attendance System.
"""

# ---------------------------------------------------------------------------
# Admin users
# ---------------------------------------------------------------------------
ADMIN_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
STUDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_number TEXT UNIQUE NOT NULL,
    image_path TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""

# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
ATTENDANCE_TABLE = """
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Present',
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
    UNIQUE (student_id, date)
)
"""

ALL_TABLES = (ADMIN_USERS_TABLE, STUDENTS_TABLE, ATTENDANCE_TABLE)
