import re
import traceback

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest

from app.db import add_student, delete_student, get_student_by_roll, mark_attendance
from app.face_utils import (
    FaceLibraryError,
    cleanup_registration,
    image_from_base64,
    load_all_encodings,
    process_live_frame,
    recognize_face,
    register_student_face,
)
from app.routes.auth_routes import login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")

ROLL_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,20}$")


def _validate_registration_input(name, roll_number, image_data):
    errors = {}

    if not name or len(name.strip()) < 2:
        errors["name"] = "Name must be at least 2 characters."
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or fewer."

    if not roll_number:
        errors["roll_number"] = "Roll number is required."
    elif not ROLL_PATTERN.match(roll_number):
        errors["roll_number"] = (
            "Use 2–20 letters, numbers, hyphens, or underscores only."
        )

    if not image_data:
        errors["image"] = "Please capture a face image from the webcam."

    return errors


@api_bp.route("/register-student", methods=["POST"])
@login_required
def register_student_api():

    try:
        if request.content_type != "application/json":
            current_app.logger.warning(
                "Unexpected content type: %s",
                request.content_type
            )

        data = request.get_json(silent=False) or {}

        roll_number = (data.get("roll_number") or "").strip()
        name = (data.get("name") or "").strip()
        image_data = data.get("image")

        current_app.logger.debug(
            "Register request => name=%s roll=%s image_length=%s",
            name,
            roll_number,
            len(image_data) if image_data else None,
        )

        errors = _validate_registration_input(
            name,
            roll_number,
            image_data
        )

        if errors:
            return jsonify({
                "success": False,
                "message": "Please fix the errors below.",
                "errors": errors
            }), 400

        if get_student_by_roll(roll_number):
            return jsonify({
                "success": False,
                "message": "Roll number already exists.",
                "errors": {
                    "roll_number": "Roll number already exists."
                }
            }), 409

        image_bgr = image_from_base64(image_data)

        if image_bgr is None:
            return jsonify({
                "success": False,
                "message": "Invalid image data."
            }), 400

        try:
            image_path, _encoding = register_student_face(
                roll_number,
                image_bgr
            )

        except FaceLibraryError as exc:
            return jsonify({
                "success": False,
                "message": f"Face Library Error: {str(exc)}"
            }), 503

        except ValueError as exc:
            return jsonify({
                "success": False,
                "message": f"Validation Error: {str(exc)}",
                "errors": {
                    "image": str(exc)
                }
            }), 400

        except OSError as exc:
            return jsonify({
                "success": False,
                "message": f"File Error: {str(exc)}"
            }), 500

        except Exception as exc:
            current_app.logger.error(traceback.format_exc())

            return jsonify({
                "success": False,
                "message": f"Unexpected Error: {str(exc)}",
                "trace": traceback.format_exc()
            }), 500

        ok, db_error = add_student(
            name,
            roll_number,
            image_path
        )

        if not ok:
            cleanup_registration(roll_number)

            return jsonify({
                "success": False,
                "message": db_error
            }), 400

        return jsonify({
            "success": True,
            "message": f"Student '{name}' registered successfully!",
            "data": {
                "name": name,
                "roll_number": roll_number,
                "image_path": image_path
            }
        }), 201

    except Exception as exc:

        current_app.logger.error(traceback.format_exc())

        return jsonify({
            "success": False,
            "message": f"SERVER ERROR: {str(exc)}",
            "trace": traceback.format_exc()
        }), 500


@api_bp.route("/recognize", methods=["POST"])
@login_required
def recognize_api():

    data = request.get_json(silent=True) or {}

    image_data = data.get("image")

    if not image_data:
        return jsonify({
            "success": False,
            "message": "Image required"
        }), 400

    image_bgr = image_from_base64(image_data)

    if image_bgr is None:
        return jsonify({
            "success": False,
            "message": "Invalid image"
        }), 400

    result = recognize_face(image_bgr)

    return jsonify(result)


@api_bp.route("/recognize-live", methods=["POST"])
@login_required
def recognize_live_api():

    data = request.get_json(silent=True) or {}

    image_data = data.get("image")

    if not image_data:
        return jsonify({
            "success": False,
            "message": "Image required"
        }), 400

    image_bgr = image_from_base64(image_data)

    result = process_live_frame(
        image_bgr,
        auto_mark=True
    )

    return jsonify(result)


@api_bp.route("/students/<roll_number>", methods=["DELETE"])
@login_required
def remove_student(roll_number):

    from app.face_utils import (
        delete_face_image,
        delete_encoding
    )

    student = get_student_by_roll(
        roll_number
    )

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    delete_student(
        roll_number
    )

    delete_face_image(
        roll_number
    )

    delete_encoding(
        roll_number
    )

    return jsonify({
        "success": True,
        "message": "Student removed"
    })