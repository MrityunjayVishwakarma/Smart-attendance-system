import os
import pickle
import re
import numpy as np

from app.config import Config


class FaceLibraryError(Exception):
    """Raised when face_recognition or OpenCV is not available."""

    pass


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError as exc:
        raise FaceLibraryError(
            "OpenCV is not installed. Run: pip install opencv-python"
        ) from exc


def _np():
    try:
        import numpy as np
        return np
    except ImportError as exc:
        raise FaceLibraryError(
            "NumPy is not installed. Run: pip install numpy"
        ) from exc


def _face_recognition():
    try:
        import face_recognition
        return face_recognition
    except ImportError as exc:
        raise FaceLibraryError(
            "face_recognition is not installed. Run: pip install face-recognition"
        ) from exc


def sanitize_roll_number(roll_number):
    """Return a filesystem-safe roll number for image/encoding filenames."""
    safe = re.sub(r"[^\w\-]", "_", roll_number.strip())
    return safe or "student"


def encoding_path(roll_number):
    safe_id = sanitize_roll_number(roll_number)
    return os.path.join(Config.ENCODINGS_FOLDER, f"{safe_id}.pkl")


def dataset_image_path(roll_number):
    safe_id = sanitize_roll_number(roll_number)
    return os.path.join(Config.DATASET_FOLDER, f"{safe_id}.jpg")

def image_from_base64(data_url):
    import base64

    cv2 = _cv2()

    if not data_url:
        return None

    # Remove base64 header if present
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]

    data_url = "".join(data_url.split())

    try:
        image_bytes = base64.b64decode(data_url)
    except Exception:
        return None

    if not image_bytes:
        return None

    # Convert bytes → numpy array
    nparr = np.frombuffer(image_bytes, dtype=np.uint8)

    try:
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return None

    return image



def save_face_image(roll_number, image_bgr):
    """Save captured face image to the dataset folder."""
    cv2 = _cv2()
    os.makedirs(Config.DATASET_FOLDER, exist_ok=True)
    file_path = dataset_image_path(roll_number)
    if not cv2.imwrite(file_path, image_bgr):
        raise OSError("Failed to write image to dataset folder.")
    safe_id = sanitize_roll_number(roll_number)
    return f"dataset/{safe_id}.jpg"


def delete_face_image(roll_number):
    file_path = dataset_image_path(roll_number)
    if os.path.exists(file_path):
        os.remove(file_path)


def create_encoding(image_bgr):
    """Generate a 128-dimensional face encoding using face_recognition."""
    cv2 = _cv2()
    face_recognition = _face_recognition()
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if not locations:
        return None, "No face detected. Please face the camera clearly."
    if len(locations) > 1:
        return None, "Multiple faces detected. Only one person should be in the frame."

    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    if not encodings:
        return None, "Could not generate face encoding. Try better lighting."

    return encodings[0], None


def save_encoding(roll_number, encoding):
    os.makedirs(Config.ENCODINGS_FOLDER, exist_ok=True)
    path = encoding_path(roll_number)
    with open(path, "wb") as file:
        pickle.dump(encoding, file)


def delete_encoding(roll_number):
    path = encoding_path(roll_number)
    if os.path.exists(path):
        os.remove(path)


def register_student_face(roll_number, image_bgr):
    """
    Full registration pipeline: validate face, save dataset image, create encoding.
    Returns (image_path, encoding) on success or raises ValueError with message.
    """
    encoding, error = create_encoding(image_bgr)
    if error:
        raise ValueError(error)

    image_path = save_face_image(roll_number, image_bgr)
    try:
        save_encoding(roll_number, encoding)
    except OSError as exc:
        delete_face_image(roll_number)
        raise OSError("Failed to save face encoding.") from exc

    return image_path, encoding


def cleanup_registration(roll_number):
    """Remove dataset image and encoding after a failed database insert."""
    delete_face_image(roll_number)
    delete_encoding(roll_number)


def load_all_encodings():
    roll_numbers = []
    encodings = []
    students = []

    if not os.path.isdir(Config.ENCODINGS_FOLDER):
        return roll_numbers, encodings, students

    from app.db import get_student_by_encoding_key

    for filename in os.listdir(Config.ENCODINGS_FOLDER):
        if not filename.endswith(".pkl"):
            continue
        roll_key = filename[:-4]
        path = os.path.join(Config.ENCODINGS_FOLDER, filename)
        with open(path, "rb") as file:
            encodings.append(pickle.load(file))
            roll_numbers.append(roll_key)
            student = get_student_by_encoding_key(roll_key)
            students.append(student)

    return roll_numbers, encodings, students


def process_live_frame(image_bgr, auto_mark=True):
    """
    Real-time face detection and recognition on a single video frame.
    Detects all faces, matches registered students, optionally marks attendance.
    Returns face bounding boxes and recognition results for overlay display.
    """
    from app.db import mark_attendance as save_attendance

    cv2 = _cv2()
    face_recognition = _face_recognition()

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    height, width = image_bgr.shape[:2]

    face_locations = face_recognition.face_locations(rgb, model="hog")
    if not face_locations:
        return {
            "success": True,
            "faces": [],
            "frame_width": width,
            "frame_height": height,
            "message": "No face detected",
        }

    face_encodings = face_recognition.face_encodings(rgb, face_locations)
    known_rolls, known_encodings, known_students = load_all_encodings()

    results = []
    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        face = {
            "top": int(top),
            "right": int(right),
            "bottom": int(bottom),
            "left": int(left),
            "name": "Unknown",
            "roll_number": None,
            "recognized": False,
            "confidence": 0.0,
            "attendance_marked": False,
            "attendance_message": "",
        }

        if known_encodings:
            matches = face_recognition.compare_faces(
                known_encodings,
                encoding,
                tolerance=Config.FACE_MATCH_TOLERANCE,
            )
            distances = face_recognition.face_distance(known_encodings, encoding)

            if True in matches:
                best_index = int(np.argmin(distances))
                if matches[best_index]:
                    student = known_students[best_index]
                    if student:
                        face["recognized"] = True
                        face["name"] = student["name"]
                        face["roll_number"] = student["roll_number"]
                        face["confidence"] = round(1 - float(distances[best_index]), 2)

                        if auto_mark:
                            marked, detail = save_attendance(
                                student["id"], student["name"]
                            )
                            face["attendance_marked"] = marked
                            face["attendance_message"] = (
                                "Attendance Marked"
                                if marked
                                else detail
                            )

        results.append(face)

    return {
        "success": True,
        "faces": results,
        "frame_width": width,
        "frame_height": height,
    }


def recognize_face(image_bgr):
    """Single-face recognition (legacy endpoint)."""
    frame_result = process_live_frame(image_bgr, auto_mark=False)
    if not frame_result.get("faces"):
        return {"success": False, "message": frame_result.get("message", "No face detected.")}

    if len(frame_result["faces"]) > 1:
        return {"success": False, "message": "Multiple faces detected. Only one person in frame."}

    face = frame_result["faces"][0]
    if not face["recognized"]:
        return {"success": False, "message": "Face not recognized. Please register first."}

    from app.db import get_student_by_roll

    student = get_student_by_roll(face["roll_number"])
    return {
        "success": True,
        "student_pk": student["id"] if student else None,
        "roll_number": face["roll_number"],
        "name": face["name"],
        "confidence": face["confidence"],
    }
