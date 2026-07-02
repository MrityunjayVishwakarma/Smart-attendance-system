import os
import sqlite3

from flask import g
from werkzeug.security import generate_password_hash

from app.config import Config
from app.models import ALL_TABLES


def get_db():
    """Return a per-request SQLite connection stored on Flask's `g` object."""
    if "db" not in g:
        g.db = sqlite3.connect(
            Config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_connection():
    """Standalone connection for scripts or app startup (outside request context)."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _table_columns(conn, table_name):
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}
    except sqlite3.OperationalError:
        return set()


def _existing_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def is_old_schema(conn):
    """Return True if the database uses the pre-migration schema."""
    tables = _existing_tables(conn)
    if not tables:
        return False

    if "admin" in tables:
        return True

    if "students" in tables:
        cols = _table_columns(conn, "students")
        if "roll_number" not in cols or "image_path" not in cols:
            return True
        if "student_id" in cols or "face_image_path" in cols:
            return True

    if "attendance" in tables:
        cols = _table_columns(conn, "attendance")
        if "date" not in cols or "time" not in cols or "name" not in cols:
            return True
        if "attendance_date" in cols or "attendance_time" in cols:
            return True

    if "admin_users" not in tables and tables:
        return True

    return False


def remove_old_database():
    """Delete the SQLite file so tables can be recreated with the new schema."""
    if os.path.exists(Config.DATABASE_PATH):
        os.remove(Config.DATABASE_PATH)
        return True
    return False


def migrate_if_needed():
    """
    Detect an outdated schema and remove the database file.
    Returns True if the database was removed.
    """
    if not os.path.exists(Config.DATABASE_PATH):
        return False

    conn = get_connection()
    try:
        outdated = is_old_schema(conn)
    finally:
        conn.close()

    if outdated:
        remove_old_database()
        return True
    return False


def init_db():
    """Create tables and seed the default admin user."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
    os.makedirs(Config.ENCODINGS_FOLDER, exist_ok=True)

    removed = migrate_if_needed()
    if removed:
        print("[database] Removed outdated attendance.db — recreating with new schema.")

    conn = get_connection()
    cursor = conn.cursor()

    for table_sql in ALL_TABLES:
        cursor.execute(table_sql)

    cursor.execute("SELECT COUNT(*) AS count FROM admin_users")
    if cursor.fetchone()["count"] == 0:
        from datetime import datetime

        cursor.execute(
            """
            INSERT INTO admin_users (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (
                Config.DEFAULT_ADMIN_USERNAME,
                generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD),
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()


def init_app(app):
    """Register database helpers with the Flask application."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
