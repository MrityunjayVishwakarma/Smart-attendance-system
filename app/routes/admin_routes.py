import os
from io import BytesIO

from flask import Blueprint, render_template, send_from_directory, send_file, request, abort

from app.config import Config
from app.db import (
    get_all_students,
    get_attendance_records,
    get_dashboard_stats,
    get_all_attendance_records,
)
from app.routes.auth_routes import login_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)


@admin_bp.route("/students")
@login_required
def students():
    students_list = get_all_students()
    return render_template("students.html", students=students_list)


@admin_bp.route("/register")
@login_required
def register_student():
    return render_template("register_student.html")


@admin_bp.route("/attendance")
@login_required
def mark_attendance():
    return render_template("mark_attendance.html")


@admin_bp.route("/records")
@login_required
def records():
    # Read filter and pagination params from query string
    date_filter = request.args.get("date") or None
    name_filter = request.args.get("name") or None
    roll_filter = request.args.get("roll_number") or None

    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    try:
        per_page = int(request.args.get("per_page", 200))
        if per_page < 1:
            per_page = 200
    except ValueError:
        per_page = 200

    offset = (page - 1) * per_page

    records_list = get_attendance_records(limit=per_page, offset=offset, date=date_filter, name=name_filter, roll_number=roll_filter)

    filters = {
        "date": date_filter or "",
        "name": name_filter or "",
        "roll_number": roll_filter or "",
        "page": page,
        "per_page": per_page,
    }

    return render_template("records.html", records=records_list, filters=filters)


@admin_bp.route("/export-attendance")
@login_required
def export_attendance():
    """Export all attendance records to an .xlsx file and return it as a download."""
    records = get_all_attendance_records()

    try:
        from openpyxl import Workbook
    except ImportError:
        abort(503, description="openpyxl is not installed. Install dependencies with 'pip install -r requirements.txt'.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # Header row (order: Student Name, Roll Number, Date, Time, Status)
    ws.append(["Student Name", "Roll Number", "Date", "Time", "Status"])

    for r in records:
        ws.append([r.get("name"), r.get("roll_number"), r.get("date"), r.get("time"), r.get("status")])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = "attendance_records.xlsx"
    return send_file(
        stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@admin_bp.route("/dataset/<path:filename>")
@login_required
def dataset_image(filename):
    """Serve face images from the dataset folder."""
    safe_name = os.path.basename(filename)
    return send_from_directory(Config.DATASET_FOLDER, safe_name)
