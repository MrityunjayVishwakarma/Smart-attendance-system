# Smart Attendance System

A face-recognition based attendance system built with **Python Flask**, **OpenCV**, **face_recognition**, **SQLite**, and a modern **HTML/CSS/JavaScript** admin UI.

## Features

- Student face registration via webcam
- Real-time face recognition for attendance
- Automatic attendance marking (once per student per day)
- Admin dashboard with daily statistics
- Attendance records with date and time
- Secure admin login
- Clean, responsive dark-themed UI

## Project Structure

```
Smart-Attendance-System/
├── run.py                      # Application entry point
├── requirements.txt
├── app/
│   ├── __init__.py             # Flask app factory
│   ├── config.py               # Configuration
│   ├── db.py                   # SQLite database layer
│   ├── face_utils.py           # Face encoding & recognition
│   └── routes/
│       ├── auth_routes.py      # Login / logout
│       ├── admin_routes.py     # Dashboard pages
│       └── api_routes.py       # REST API for webcam
├── templates/                  # HTML templates
├── static/
│   ├── css/style.css
│   ├── js/                     # Webcam & UI scripts
│   └── uploads/faces/          # Student photos
├── data/encodings/             # Face encoding files (.pkl)
└── instance/attendance.db      # SQLite database (auto-created)
```

## Prerequisites

- Python 3.10 or 3.11 (recommended; 3.12+ may have issues with `dlib`)
- Webcam
- **Windows**: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) for compiling `dlib` if pip install fails

### Alternative: Pre-built dlib (Windows)

```bash
pip install dlib-binary
pip install face-recognition
```

## Installation

1. **Clone or open the project folder**

2. **Create a virtual environment**

```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

If `face-recognition` fails on Windows, try:

```bash
pip install cmake
pip install dlib
pip install -r requirements.txt
```

4. **Run the application**

```bash
python run.py
```

5. **Open in browser**

```
http://127.0.0.1:5000
```

## Default Admin Login

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

Change the default password in production by updating the admin record in the database.

## Usage Guide

1. **Login** as admin
2. **Register Student** — enter ID and name, capture face from webcam, submit
3. **Mark Attendance** — start scanning; recognized students are marked present automatically
4. **Students** — view or delete registered profiles
5. **Attendance Records** — view full history with date and time

## API Endpoints

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| POST   | `/api/register-student`   | Register student + face  |
| POST   | `/api/recognize`          | Recognize & mark attendance |
| DELETE | `/api/students/<id>`      | Remove student           |

## Technology Stack

- **Backend**: Flask, SQLite, Werkzeug (password hashing)
- **Face AI**: OpenCV, face_recognition (dlib)
- **Frontend**: HTML5, CSS3, JavaScript (MediaDevices API)

## Security Notes

- Set `SECRET_KEY` environment variable in production
- Use HTTPS when deploying
- Restrict camera access to trusted admin devices
- Replace default admin credentials before deployment

## License

MIT — free for educational and personal use.
