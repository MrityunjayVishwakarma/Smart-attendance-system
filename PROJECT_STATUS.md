# Project Status: Smart Attendance System

## Overview

This repository is a Python Flask-based attendance system using webcam face recognition. Although the request mentioned Django, the project is implemented with Flask, not Django.

Key technologies:

- Flask 3.0.3
- SQLite
- OpenCV
- face_recognition (dlib-based)
- HTML/CSS/JavaScript
- Werkzeug password hashing

## Project Structure

- `run.py` — application entry point
- `requirements.txt` — Python dependencies
- `app/__init__.py` — Flask application factory and blueprint registration
- `app/config.py` — application configuration paths and settings
- `app/database.py` — SQLite initialization, migration detection, and request lifecycle management
- `app/db.py` — CRUD data access layer for admin, students, attendance
- `app/models.py` — SQL schema definitions for `admin_users`, `students`, and `attendance`
- `app/face_utils.py` — webcam image decoding, face encoding, registration, live recognition, and image persistence
- `app/routes/auth_routes.py` — login/logout and session gating
- `app/routes/admin_routes.py` — Flask pages for dashboard, registration, attendance, records, and student list
- `app/routes/api_routes.py` — AJAX endpoints for registration, recognition, live recognition, and student deletion
- `static/js` — webcam capture, register workflow, real-time attendance workflow
- `templates/` — UI templates for login, dashboard, student registration, attendance, records, and student list
- `dataset/` — stored student face images
- `data/encodings/` — serialized face encoding files
- `instance/attendance.db` — SQLite database file (created at runtime)

## Completed Features

### Authentication

- Admin login via `/login`
- Session-based login required enforcement on admin pages and API routes
- Logout support

### Student management

- Register student with name and roll number
- Capture face image from webcam
- Store image in `dataset/` and encoding in `data/encodings/`
- View registered students
- Delete students, including image and encoding cleanup

### Attendance marking

- Live webcam attendance scanning page
- Face detection and recognition with bounding boxes
- Automatic attendance marking once per student per day
- Attendance records listing
- Dashboard metrics: total students, today’s attendance, total records, recent today

### Face recognition backend

- Single-face registration encoding
- Multi-face live frame processing
- Recognition confidence scoring
- Duplicate face prevention per day

### Database and persistence

- SQLite tables created automatically on startup
- Default admin seed user inserted if none exists
- Foreign keys enabled with attendance referencing students
- Migration detection for old schema versions

## Database Schema

### `admin_users`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT UNIQUE NOT NULL
- `password_hash` TEXT NOT NULL
- `created_at` TEXT NOT NULL

### `students`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `name` TEXT NOT NULL
- `roll_number` TEXT UNIQUE NOT NULL
- `image_path` TEXT NOT NULL
- `created_at` TEXT NOT NULL

### `attendance`

- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `student_id` INTEGER NOT NULL
- `name` TEXT NOT NULL
- `date` TEXT NOT NULL
- `time` TEXT NOT NULL
- `status` TEXT NOT NULL DEFAULT 'Present'
- foreign key `student_id` references `students(id)` ON DELETE CASCADE
- unique constraint on `(student_id, date)` to prevent duplicate daily marks

## Pending Features and Enhancements

- Student edit/update flow is not present
- Attendance export (CSV/Excel) is missing
- Records filtering by date, student, or status is absent
- Multi-admin user management is not implemented
- Password change/reset functionality is missing
- Admin UI lacks explicit account/security settings
- No role-based access beyond single admin login
- No audit trail for deleted or modified students
- No data backup or export/import capability
- No explicit input validation or sanitization on templates aside from client-side JS
- No unit or integration tests are present in the repository
- No Docker or deployment manifest is included

## Bugs, Risks, and Observations

### Security and hardening

- Default credentials are seeded as `admin/admin123`
- No CSRF protection is configured for form posts
- `SECRET_KEY` falls back to a hardcoded default unless set in env
- Session protection and secure cookie settings are not visible in config

### Reliability

- `get_student_by_encoding_key()` scans all students on each call, which may become slow as records grow
- `process_live_frame()` loads encodings each request; this could be optimized by caching encodings in memory
- Live scanning interval is fixed to 1500ms; performance may vary on slower machines
- If image saving or encoding fails after student DB insertion, cleanup is attempted but may not cover all partial failure cases

### Usability

- The attendance page requires starting the camera manually each time
- No explicit manual attendance override exists for unidentified or missed scans
- Deleting a student removes the DB row and files, but there is no confirmation flow indicated in server-side logic

### Technology mismatch

- The codebase is Flask-based, not Django-based. If the expectation is Django, a rewrite or migration is required.

## Recommended Next Steps

1. Add tests
   - Add unit tests for `app/db.py`, `app/face_utils.py`, and `app/routes/api_routes.py`
   - Add integration tests for authorization, registration, attendance marking, and deletion

2. Harden security
   - Enable CSRF protection for forms
   - Require `SECRET_KEY` from environment in production
   - Add admin password reset/change flow
   - Configure secure cookie settings and session expiration

3. Improve attendance features
   - Add date/student filters and export for attendance records
   - Add student edit/update functionality
   - Add manual attendance override or absent marking

4. Optimize recognition
   - Cache loaded face encodings instead of reading from disk on every recognition request
   - Add configuration for face-recognition model or tolerance

5. Prepare deployment
   - Add Docker support or deployment scripts
   - Add README section for production deployment and environment variables
   - Consider HTTPS and hosted camera requirements

6. Clarify architecture and README
   - Update documentation to reflect Flask implementation clearly
   - Add developer notes for where face images, encodings, and the DB are stored

## File Recommendations

- `app/config.py` — add environment-based configuration and production flags
- `app/database.py` — improve migration strategy and DB schema versioning
- `app/face_utils.py` — separate model loading and recognition for caching
- `app/routes/api_routes.py` — add more API response consistency and errors mapping

## Conclusion

The project is functionally complete for a basic face-recognition attendance system using Flask. It can be improved by adding security hardening, admin/user management, attendance export/filtering, tests, and deployment readiness.
