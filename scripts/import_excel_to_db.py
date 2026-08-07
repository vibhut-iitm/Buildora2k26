import sys
import os
import pandas as pd
import hashlib

# Ensure backend folder is in path for db import
sys.path.append(os.path.join(os.getcwd(), "backend"))
from db import db

excel_path = r"C:\Users\pc\Downloads\Buildora2k26\student details\Hackethon final list.xlsx"

def generate_token(team_name, member_name, email):
    # Deterministic token generation
    base_str = f"{str(team_name).lower().strip()}_{str(member_name).lower().strip()}_{str(email).lower().strip()}"
    return hashlib.sha256(base_str.encode('utf-8')).hexdigest()[:8]

def run_import():
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return

    print(f"Reading Excel sheet: {excel_path} ...")
    df = pd.read_excel(excel_path)

    # Let's delete all existing records in database (SQLite or Supabase depending on config)
    print(f"Deleting all existing records from the database (Mode: {db.mode})...")
    db.delete_all()

    count = 0
    skipped = 0

    # To generate sequential REG IDs and Team IDs
    team_ids = {}
    team_counter = 1

    for idx, row in df.iterrows():
        team_name = row.get("Team Name")
        member_name = row.get("Team Member Name")
        num_members = row.get("Number of Team Members")
        year_branch = row.get("Year & Branch")
        email = row.get("Email Address")

        # Skip rows where member name is invalid or placeholder
        if pd.isna(member_name) or not str(member_name).strip() or str(member_name).strip() in ["____", "___", "--", "-"]:
            skipped += 1
            continue

        # Clean NaN values
        team_name = str(team_name).strip() if not pd.isna(team_name) else "Individual"
        member_name = str(member_name).strip()
        year_branch = str(year_branch).strip() if not pd.isna(year_branch) else "N/A"
        email = str(email).strip() if not pd.isna(email) else ""

        # Map Team ID
        if team_name not in team_ids:
            team_ids[team_name] = f"T-{team_counter:03d}"
            team_counter += 1
        team_id = team_ids[team_name]

        token = generate_token(team_name, member_name, email)
        reg_id = f"REG-{idx+1:03d}"

        student_data = {
            "qr_token": token,
            "token": token,
            "registration_id": reg_id,
            "team_id": team_id,
            "team_name": team_name,
            "participant_name": member_name,
            "student_name": member_name,
            "participant_email": email,
            "email": email,
            "college_name": year_branch,
            "Branch": year_branch,
            "participant_role": "Participant"
        }

        db.insert(student_data)
        count += 1
        if count % 10 == 0:
            print(f"Imported {count} students...")

    print(f"\nImport Finished successfully!")
    print(f"Total students imported: {count}")
    print(f"Total rows skipped (empty/placeholders): {skipped}")

if __name__ == "__main__":
    run_import()
