from flask import Blueprint, request, jsonify
import uuid
from db import db

generate_bp = Blueprint("generate", __name__)

@generate_bp.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    name = data.get("student_name")
    branch = data.get("branch", "N/A")

    if not name:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    token = str(uuid.uuid4())[:8]

    try:
        db.insert({
            "token": token,
            "student_name": name,
            "Status": "Valid",
            "Branch": branch
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "created",
        "token": token,
        "student_name": name
    })