import sqlite3
from datetime import date, datetime

from werkzeug.security import check_password_hash

from app.database import get_db


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
def verify_admin(username, password):
    db = get_db()
    row = db.execute(
        "SELECT * FROM admin_users WHERE username = ?", (username,)
    ).fetchone()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
def add_student(name, roll_number, image_path):
    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO students (name, roll_number, image_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, roll_number, image_path, datetime.now().isoformat()),
        )
        db.commit()
        return True, None
    except sqlite3.IntegrityError:
        db.rollback()
        return False, "Roll number already exists."


def get_all_students():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM students ORDER BY created_at DESC"
    ).fetchall()
    return [dict(row) for row in rows]


def get_student_by_roll(roll_number):
    db = get_db()
    row = db.execute(
        "SELECT * FROM students WHERE roll_number = ?", (roll_number,)
    ).fetchone()
    return dict(row) if row else None


def get_student_by_encoding_key(encoding_key):
    """Find student whose sanitized roll number matches an encoding filename key."""
    from app.face_utils import sanitize_roll_number

    for student in get_all_students():
        if sanitize_roll_number(student["roll_number"]) == encoding_key:
            return student
    return None


def get_student_by_pk(student_pk):
    db = get_db()
    row = db.execute(
        "SELECT * FROM students WHERE id = ?", (student_pk,)
    ).fetchone()
    return dict(row) if row else None


def delete_student(roll_number):
    student = get_student_by_roll(roll_number)
    if not student:
        return

    db = get_db()
    db.execute("DELETE FROM students WHERE roll_number = ?", (roll_number,))
    db.commit()


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
def mark_attendance(student_pk, name, status="Present"):
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    db = get_db()
    existing = db.execute(
        """
        SELECT id FROM attendance
        WHERE student_id = ? AND date = ?
        """,
        (student_pk, today),
    ).fetchone()

    if existing:
        return False, "Already marked present today."

    db.execute(
        """
        INSERT INTO attendance (student_id, name, date, time, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (student_pk, name, today, now, status),
    )
    db.commit()
    return True, now


def get_attendance_records(limit=200, offset=0, date=None, name=None, roll_number=None):
    """Return attendance records with optional filtering and pagination.

    Parameters:
    - limit: max rows to return (keeps existing behavior when called without args)
    - offset: number of rows to skip (for pagination)
    - date: filter by exact `date` string (ISO format YYYY-MM-DD)
    - name: case-insensitive partial match against attendance.name
    - roll_number: case-insensitive partial match against students.roll_number
    """
    db = get_db()

    base_sql = (
        "SELECT a.id, a.student_id, s.roll_number, a.name, a.date, a.time, a.status"
        " FROM attendance a JOIN students s ON s.id = a.student_id"
    )

    where_clauses = []
    params = []

    if date:
        where_clauses.append("a.date = ?")
        params.append(date)
    if name:
        where_clauses.append("LOWER(a.name) LIKE ?")
        params.append(f"%{name.lower()}%")
    if roll_number:
        where_clauses.append("LOWER(s.roll_number) LIKE ?")
        params.append(f"%{roll_number.lower()}%")

    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)

    base_sql += " ORDER BY a.date DESC, a.time DESC"
    base_sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.execute(base_sql, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def get_all_attendance_records():
    """Return all attendance records without a result limit.

    This helper is used by the XLSX export feature to retrieve a complete
    history of attendance records while leaving `get_attendance_records`
    behavior unchanged for the UI (which still uses a limited result set).
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT a.id, a.student_id, s.roll_number, a.name, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.date DESC, a.time DESC
        """,
    ).fetchall()
    return [dict(row) for row in rows]


def get_dashboard_stats():
    db = get_db()
    today = date.today().isoformat()

    total_students = db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    today_attendance = db.execute(
        "SELECT COUNT(*) AS c FROM attendance WHERE date = ?", (today,)
    ).fetchone()["c"]
    total_records = db.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()["c"]

    recent = db.execute(
        """
        SELECT s.roll_number, a.name, a.time
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        WHERE a.date = ?
        ORDER BY a.time DESC
        LIMIT 8
        """,
        (today,),
    ).fetchall()

    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "total_records": total_records,
        "recent_today": [dict(row) for row in recent],
    }
