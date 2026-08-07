from flask import Blueprint, jsonify, request
from db import db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Buildora backend is awake and healthy!"})

@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    try:
        stats = db.count_stats()
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/passes", methods=["GET"])
def get_passes():
    try:
        rows = db.fetch_all()
        data = []
        for r in rows:
            status_text = r.get("Status", "Valid")
            is_used = status_text == "Checked In" or r.get("used", False)
            branch = r.get("branch") or r.get("Branch", "N/A")

            if isinstance(branch, str) and branch.startswith("\\x"):
                try:
                    branch = bytes.fromhex(branch[2:]).decode('utf-8')
                except:
                    pass

            data.append({
                "student_name": r.get("participant_name") or r.get("student_name", "Unknown"),
                "participant_name": r.get("participant_name") or r.get("student_name", "Unknown"),
                "team_name": r.get("team_name", "N/A"),
                "branch": branch,
                "used": is_used,
                "attendance_status": "Present" if is_used else "Pending",
                "check_in_time": r.get("CheckInTime") or r.get("check_in_time")
            })
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/reset", methods=["POST"])
def reset_passes():
    try:
        db.reset_all()
        return jsonify({"status": "success", "message": "All passes have been reset."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/delete-all", methods=["POST"])
def delete_all_passes():
    try:
        db.delete_all()
        return jsonify({"status": "success", "message": "All passes have been deleted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route("/db-settings", methods=["POST"])
def update_db_settings():
    data = request.get_json() or {}
    mode = data.get("mode")
    if mode not in ["sqlite", "supabase"]:
        return jsonify({"status": "error", "message": "Invalid mode"}), 400
    db.mode = mode
    return jsonify({"status": "success", "mode": mode})
