from flask import Blueprint, request, jsonify
import csv
import io
import uuid
import hashlib
from db import db

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    file_bytes = file.stream.read()
    
    try:
        content = file_bytes.decode("utf-8-sig")  # handles UTF-8 BOM
    except UnicodeDecodeError:
        content = file_bytes.decode("latin-1", errors="replace") # fallback
        
    stream = io.StringIO(content, newline=None)
    csv_reader = csv.DictReader(stream)

    inserted = []
    count = 0

    try:
        # Clear database for clean upload
        db.delete_all()

        for row in csv_reader:
            # Map robust column headers
            name = row.get("participant_name") or row.get("student_name") or row.get("name") or row.get("Participant Name")
            branch = row.get("branch") or row.get("Branch") or row.get("team_name") or row.get("Team Name") or "General"
            college = row.get("college") or row.get("college_name") or row.get("College") or "N/A"
            token = row.get("qr_token") or row.get("token") or row.get("Registration ID") or row.get("registration_id")

            if not name:
                continue

            # Auto-generate token if missing
            if not token:
                base_str = f"{name.strip().lower()}-{branch.strip().lower()}-{count}"
                token = hashlib.sha256(base_str.encode()).hexdigest()[:8]

            db.insert({
                "token": token,
                "participant_name": name,
                "student_name": name,
                "Branch": branch,
                "team_name": branch,
                "college_name": college,
                "college": college
            })

            inserted.append({
                "student_name": name,
                "token": token
            })
            count += 1
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({
        "status": "success",
        "total_uploaded": len(inserted),
        "data": inserted
    })