from flask import Blueprint, request, jsonify
from db import db

verify_bp = Blueprint("verify", __name__)

@verify_bp.route("/verify", methods=["POST"])
def verify():
    data = request.get_json() or {}
    token = data.get("token")
    action = data.get("action", "lookup")  # "lookup", "mark", or "auto"
    mode = data.get("mode", "entry")

    if not token:
        return jsonify({"status": "invalid", "message": "No QR token provided"})

    try:
        participant = db.find_by_token(token)
        if not participant:
            return jsonify({"status": "invalid", "message": "UNREGISTERED / FAKE PASS"})

        name = participant.get("participant_name") or participant.get("student_name", "Unknown")
        reg_id = participant.get("registration_id") or token
        team_name = participant.get("team_name") or participant.get("branch") or participant.get("Branch", "N/A")
        college = participant.get("college") or participant.get("college_name") or "IERT Prayagraj"
        role = participant.get("role") or participant.get("participant_role") or "Participant"
        is_used = participant.get("used", False) or participant.get("Status") == "Checked In" or participant.get("attendance_status") in ["Present", "Checked In"]
        check_in_time = participant.get("check_in_time") or participant.get("CheckInTime")

        # 1. Refreshment mode handling
        if mode == "refreshment":
            current_refreshment = participant.get("RefreshmentStatus")
            if current_refreshment == "Claimed":
                claim_time = participant.get("RefreshmentTime") or "Unknown"
                return jsonify({
                    "status": "used",
                    "name": name,
                    "registration_id": reg_id,
                    "team_name": team_name,
                    "college": college,
                    "role": role,
                    "check_in_time": claim_time,
                    "message": f"Refreshment Already Claimed at {claim_time}!"
                })
            
            if action == "mark" or action == "auto":
                db.update_refreshment_status(token, "Claimed")
                from datetime import datetime, timedelta
                now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
                return jsonify({
                    "status": "valid",
                    "name": name,
                    "registration_id": reg_id,
                    "team_name": team_name,
                    "college": college,
                    "role": role,
                    "check_in_time": now,
                    "message": f"Refreshment Claimed Successfully at {now}!"
                })
            else:
                return jsonify({
                    "status": "lookup_success",
                    "name": name,
                    "registration_id": reg_id,
                    "team_name": team_name,
                    "college": college,
                    "role": role,
                    "attendance_status": "Claimed" if current_refreshment == "Claimed" else "Pending",
                    "already_checked_in": current_refreshment == "Claimed",
                    "check_in_time": participant.get("RefreshmentTime")
                })

        # 2. Main Entry Mode Handling
        if action == "mark" or action == "auto":
            if is_used:
                return jsonify({
                    "status": "used",
                    "name": name,
                    "registration_id": reg_id,
                    "team_name": team_name,
                    "college": college,
                    "role": role,
                    "already_checked_in": True,
                    "check_in_time": check_in_time or "Already Checked In"
                })

            db.update_status(token, "Checked In")
            from datetime import datetime, timedelta
            now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%I:%M %p")
            
            return jsonify({
                "status": "valid",
                "name": name,
                "registration_id": reg_id,
                "team_name": team_name,
                "college": college,
                "role": role,
                "already_checked_in": False,
                "check_in_time": now,
                "message": "Attendance Marked Successfully"
            })
        else:
            # Simple lookup (two-step scan verification)
            return jsonify({
                "status": "used" if is_used else "valid_lookup",
                "name": name,
                "registration_id": reg_id,
                "team_name": team_name,
                "college": college,
                "role": role,
                "already_checked_in": is_used,
                "attendance_status": "Present" if is_used else "Pending",
                "check_in_time": check_in_time
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500