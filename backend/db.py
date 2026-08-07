import sqlite3
import os
import requests
from config import DB_MODE, SUPABASE_URL, SUPABASE_KEY

DATABASE_LOCKED = False  # Unlocked for active event management

class Database:
    def __init__(self):
        self.mode = DB_MODE
        # Initialize SQLite configuration in all modes for automatic local fallback safety
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "passes.db"))
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.init_db()

        if self.mode == 'supabase':
            self.headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }

    def init_db(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    registration_id TEXT UNIQUE NOT NULL,
                    team_id TEXT NOT NULL,
                    team_name TEXT NOT NULL,
                    participant_name TEXT NOT NULL,
                    participant_email TEXT,
                    participant_phone TEXT,
                    college_name TEXT DEFAULT 'N/A',
                    participant_role TEXT DEFAULT 'Participant',
                    qr_token TEXT UNIQUE NOT NULL,
                    registration_status TEXT NOT NULL DEFAULT 'Confirmed',
                    attendance_status TEXT NOT NULL DEFAULT 'Pending',
                    check_in_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_qr_token ON projects(qr_token)")
            self.cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_reg_id ON projects(registration_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id)")
            
            # Seed 5 sample participants if completely empty
            self.cursor.execute("SELECT COUNT(*) FROM projects")
            if self.cursor.fetchone()[0] == 0:
                samples = [
                    ("REG001", "T-001", "Computer Science", "Rahul Sharma", "101"),
                    ("REG002", "T-001", "Computer Science", "Priya Singh", "102"),
                    ("REG003", "T-002", "Information Technology", "Amit Verma", "103"),
                    ("REG004", "T-002", "Information Technology", "Sneha Gupta", "104"),
                    ("REG005", "T-003", "Mechanical Engineering", "Arjun Yadav", "105")
                ]
                for reg_id, team_id, branch, name, token in samples:
                    import uuid
                    self.cursor.execute(
                        """INSERT INTO projects 
                           (id, registration_id, team_id, team_name, participant_name, qr_token, college_name) 
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), reg_id, team_id, branch, name, token, "IERT Prayagraj")
                    )
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS passes (
                    token TEXT PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    Status TEXT NOT NULL DEFAULT 'Valid',
                    Branch TEXT NOT NULL DEFAULT 'N/A',
                    CheckInTime TEXT
                )
            """)
            self.conn.commit()
        except Exception as e:
            print(f"DB Init Error: {e}")

    def find_by_token(self, token):
        if self.mode == 'supabase':
            try:
                # 1. Try querying projects table first
                res = requests.get(
                    f"{SUPABASE_URL}/rest/v1/Buildora2k26?qr_token=eq.{token}",
                    headers=self.headers,
                    timeout=5
                )
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    row = data[0]
                    is_present = row.get("attendance_status") in ["Present", "Checked In"]
                    return {
                        "id": row.get("id"),
                        "registration_id": row.get("registration_id"),
                        "team_id": row.get("team_id"),
                        "team_name": row.get("team_name"),
                        "participant_name": row.get("participant_name"),
                        "student_name": row.get("participant_name"),
                        "email": row.get("participant_email"),
                        "phone": row.get("participant_phone"),
                        "college": row.get("college_name", "N/A"),
                        "branch": row.get("college_name", "N/A"),
                        "role": row.get("participant_role", "Participant"),
                        "token": row.get("qr_token"),
                        "attendance_status": row.get("attendance_status", "Pending"),
                        "Status": "Checked In" if is_present else "Valid",
                        "check_in_time": row.get("check_in_time"),
                        "CheckInTime": row.get("check_in_time"),
                        "used": is_present
                    }

                # 2. Fallback to legacy passes table if not found in projects
                res_legacy = requests.get(
                    f"{SUPABASE_URL}/rest/v1/passes?token=eq.{token}",
                    headers=self.headers,
                    timeout=5
                )
                data_legacy = res_legacy.json()
                if isinstance(data_legacy, list) and len(data_legacy) > 0:
                    row = data_legacy[0]
                    is_used = row.get("Status") == "Checked In"
                    return {
                        "token": row.get("token"),
                        "registration_id": row.get("token"),
                        "team_id": "N/A",
                        "team_name": row.get("Branch", "N/A"),
                        "participant_name": row.get("student_name"),
                        "student_name": row.get("student_name"),
                        "college": "IERT Prayagraj",
                        "branch": row.get("Branch", "N/A"),
                        "role": "Participant",
                        "attendance_status": "Present" if is_used else "Pending",
                        "Status": row.get("Status", "Valid"),
                        "check_in_time": row.get("CheckInTime"),
                        "CheckInTime": row.get("CheckInTime"),
                        "used": is_used
                    }
                return None
            except Exception as e:
                print(f"Error in find_by_token: {e}")
                return None
        else:
            self.cursor.execute("SELECT * FROM projects WHERE qr_token=?", (token,))
            row = self.cursor.fetchone()
            if row:
                res = dict(row)
                is_present = res.get("attendance_status") in ["Present", "Checked In"]
                res["student_name"] = res.get("participant_name")
                res["used"] = is_present
                res["Status"] = "Checked In" if is_present else "Valid"
                res["token"] = res.get("qr_token")
                return res

            # Legacy fallback
            self.cursor.execute("SELECT * FROM passes WHERE token=?", (token,))
            row_legacy = self.cursor.fetchone()
            if row_legacy:
                res = dict(row_legacy)
                res["participant_name"] = res.get("student_name")
                res["used"] = res.get("Status") == "Checked In"
                res["attendance_status"] = "Present" if res["used"] else "Pending"
                return res
            return None

    def fetch_all(self):
        if self.mode == 'supabase':
            try:
                res = requests.get(
                    f"{SUPABASE_URL}/rest/v1/Buildora2k26?select=qr_token,participant_name,team_name,college_name,attendance_status,check_in_time,registration_id",
                    headers=self.headers,
                    timeout=8
                )
                data = res.json()
                # If table projects does not exist (PGRST205)
                if isinstance(data, dict) and data.get("code") == "PGRST205":
                    # Try legacy passes table
                    res_legacy = requests.get(
                        f"{SUPABASE_URL}/rest/v1/passes?select=token,student_name,Status,Branch,CheckInTime",
                        headers=self.headers,
                        timeout=8
                    )
                    data_legacy = res_legacy.json()
                    if isinstance(data_legacy, dict) and data_legacy.get("code") == "PGRST205":
                        # Neither table exists on Supabase -> fall back to local SQLite
                        print("Supabase tables missing. Falling back to local SQLite.")
                        return self._fetch_all_sqlite()
                    elif isinstance(data_legacy, list):
                        return [{
                            "token": row.get("token"),
                            "student_name": row.get("student_name"),
                            "participant_name": row.get("student_name"),
                            "team_name": row.get("Branch", "N/A"),
                            "branch": row.get("Branch", "N/A"),
                            "Status": row.get("Status", "Valid"),
                            "attendance_status": "Present" if row.get("Status") == "Checked In" else "Pending",
                            "CheckInTime": row.get("CheckInTime"),
                            "used": row.get("Status") == "Checked In"
                        } for row in data_legacy]
                
                if isinstance(data, list):
                    return [{
                        "token": row.get("qr_token"),
                        "student_name": row.get("participant_name"),
                        "participant_name": row.get("participant_name"),
                        "team_name": row.get("team_name"),
                        "branch": row.get("team_name", "General"),
                        "Status": "Checked In" if row.get("attendance_status") in ["Present", "Checked In"] else "Valid",
                        "attendance_status": row.get("attendance_status", "Pending"),
                        "CheckInTime": row.get("check_in_time"),
                        "used": row.get("attendance_status") in ["Present", "Checked In"]
                    } for row in data]
                
                return self._fetch_all_sqlite()
            except Exception as e:
                print(f"Supabase fetch_all error, falling back to SQLite: {e}")
                return self._fetch_all_sqlite()
        else:
            return self._fetch_all_sqlite()

    def _fetch_all_sqlite(self):
        self.cursor.execute("SELECT * FROM projects")
        rows = self.cursor.fetchall()
        if rows:
            data = [dict(row) for row in rows]
            for r in data:
                is_present = r.get("attendance_status") in ["Present", "Checked In"]
                r["student_name"] = r.get("participant_name")
                r["used"] = is_present
                r["Status"] = "Checked In" if is_present else "Valid"
                r["token"] = r.get("qr_token")
                r["branch"] = r.get("team_name")
            return data

        self.cursor.execute("SELECT * FROM passes")
        data = [dict(row) for row in self.cursor.fetchall()]
        for r in data:
            r["participant_name"] = r.get("student_name")
            r["used"] = r.get("Status") == "Checked In"
            r["attendance_status"] = "Present" if r["used"] else "Pending"
            r["branch"] = r.get("Branch")
        return data

    def count_stats(self):
        """Fast aggregated statistics query without transferring full dataset"""
        if self.mode == 'supabase':
            try:
                all_data = self.fetch_all()
                total = len(all_data)
                present = sum(1 for r in all_data if r.get("used") or r.get("attendance_status") in ["Present", "Checked In"])
                pending = total - present
                percentage = round((present / total * 100), 1) if total > 0 else 0
                return {
                    "total": total,
                    "present": present,
                    "pending": pending,
                    "percentage": percentage
                }
            except Exception as e:
                print(f"Stats calculation error: {e}")
                return {"total": 0, "present": 0, "pending": 0, "percentage": 0}
        else:
            self.cursor.execute("SELECT COUNT(*), SUM(CASE WHEN attendance_status IN ('Present', 'Checked In') THEN 1 ELSE 0 END) FROM projects")
            res = self.cursor.fetchone()
            total = res[0] if res else 0
            present = res[1] if res and res[1] else 0
            if total == 0:
                self.cursor.execute("SELECT COUNT(*), SUM(CASE WHEN Status='Checked In' THEN 1 ELSE 0 END) FROM passes")
                res_legacy = self.cursor.fetchone()
                total = res_legacy[0] if res_legacy else 0
                present = res_legacy[1] if res_legacy and res_legacy[1] else 0

            pending = total - present
            percentage = round((present / total * 100), 1) if total > 0 else 0
            return {
                "total": total,
                "present": present,
                "pending": pending,
                "percentage": percentage
            }

    def insert(self, data):
        if DATABASE_LOCKED:
            print("Block: Database is LOCKED. Insertion denied.")
            return

        token = data.get('qr_token') or data.get('token')
        name = data.get('participant_name') or data.get('student_name')
        reg_id = data.get('registration_id') or token
        team_id = data.get('team_id') or 'T-001'
        team_name = data.get('team_name') or data.get('Branch', 'N/A')
        email = data.get('participant_email', '')
        phone = data.get('participant_phone', '')
        college = data.get('college_name') or data.get('Branch', 'N/A')
        role = data.get('participant_role', 'Participant')

        if self.mode == 'supabase':
            payload = {
                "registration_id": reg_id,
                "team_id": team_id,
                "team_name": team_name,
                "participant_name": name,
                "participant_email": email,
                "participant_phone": phone,
                "college_name": college,
                "participant_role": role,
                "qr_token": token,
                "registration_status": "Confirmed",
                "attendance_status": "Pending"
            }
            try:
                res = requests.post(f"{SUPABASE_URL}/rest/v1/Buildora2k26", headers=self.headers, json=payload, timeout=5)
                # Check for missing table error
                if res.status_code == 404 or (res.status_code >= 400 and isinstance(res.json(), dict) and res.json().get("code") == "PGRST205"):
                    # Fallback to legacy passes table
                    legacy_payload = {
                        "token": token,
                        "student_name": name,
                        "Status": "Valid",
                        "Branch": team_name,
                        "CheckInTime": None
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/passes", headers=self.headers, json=legacy_payload, timeout=5)
            except Exception as e:
                print(f"Insert error: {e}")
        else:
            import uuid
            self.cursor.execute(
                """INSERT INTO projects 
                   (id, registration_id, team_id, team_name, participant_name, participant_email, participant_phone, college_name, participant_role, qr_token, registration_status, attendance_status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), reg_id, team_id, team_name, name, email, phone, college, role, token, 'Confirmed', 'Pending')
            )
            self.conn.commit()

    def update_status(self, token, status="Present"):
        from datetime import datetime, timedelta
        utc_now = datetime.utcnow()
        ist_now = utc_now + timedelta(hours=5, minutes=30)
        now_str = ist_now.strftime("%I:%M %p")
        iso_now = ist_now.isoformat()
        
        db_attendance = "Present" if status in ["Checked In", "Present"] else status

        if self.mode == 'supabase':
            # Update projects table first
            res = requests.patch(
                f"{SUPABASE_URL}/rest/v1/Buildora2k26?qr_token=eq.{token}",
                headers=self.headers,
                json={"attendance_status": db_attendance, "check_in_time": iso_now},
                timeout=5
            )
            # Also update passes legacy table for backward safety
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/passes?token=eq.{token}",
                headers=self.headers,
                json={"Status": "Checked In", "CheckInTime": now_str},
                timeout=5
            )
        else:
            self.cursor.execute("UPDATE projects SET attendance_status=?, check_in_time=? WHERE qr_token=?", (db_attendance, now_str, token))
            self.cursor.execute("UPDATE passes SET Status=?, CheckInTime=? WHERE token=?", ("Checked In", now_str, token))
            self.conn.commit()

    def reset_all(self):
        if DATABASE_LOCKED:
            print("Block: Database is LOCKED. Reset denied.")
            return

        if self.mode == 'supabase':
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/Buildora2k26?qr_token=not.is.null",
                headers=self.headers,
                json={"attendance_status": "Pending", "check_in_time": None},
                timeout=5
            )
            requests.patch(
                f"{SUPABASE_URL}/rest/v1/passes?token=not.is.null",
                headers=self.headers,
                json={"Status": "Valid", "CheckInTime": None},
                timeout=5
            )
        else:
            self.cursor.execute("UPDATE projects SET attendance_status='Pending', check_in_time=NULL")
            self.cursor.execute("UPDATE passes SET Status='Valid', CheckInTime=NULL")
            self.conn.commit()

    def delete_all(self):
        if DATABASE_LOCKED:
            print("Block: Database is LOCKED. Deletion denied.")
            return

        if self.mode == 'supabase':
            requests.delete(f"{SUPABASE_URL}/rest/v1/Buildora2k26?qr_token=not.is.null", headers=self.headers, timeout=5)
            requests.delete(f"{SUPABASE_URL}/rest/v1/passes?token=not.is.null", headers=self.headers, timeout=5)
        else:
            self.cursor.execute("DELETE FROM projects")
            self.cursor.execute("DELETE FROM passes")
            self.conn.commit()

db = Database()
