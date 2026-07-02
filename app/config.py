import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-attendance-dev-secret-change-in-production")
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "attendance.db")
    DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")
    ENCODINGS_FOLDER = os.path.join(BASE_DIR, "data", "encodings")
    FACE_MATCH_TOLERANCE = 0.5
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"
