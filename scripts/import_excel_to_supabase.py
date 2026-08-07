import os
import sys
import pandas as pd
import requests

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import SUPABASE_KEY, SUPABASE_URL

excel_path = r"C:\Users\pc\Downloads\Buildora2k26\student details\Hackethon final list.xlsx"

def import_excel_and_sync():
    if not os.path.exists(excel_path):
        print(f"Error: File not found at {excel_path}")
        return

    df = pd.read_excel(excel_path)
    clean_df = df.dropna(subset=['Team Member Name'])

    parsed = []
    for idx, row in clean_df.iterrows():
        name = str(row['Team Member Name']).strip()
        team_name = str(row['Team Name']).strip() if pd.notna(row['Team Name']) else "General"
        branch = str(row['Year & Branch']).strip() if pd.notna(row['Year & Branch']) else "N/A"
        email = str(row['Email Address']).strip() if pd.notna(row['Email Address']) else ""
        
        reg_id = f"BUILD26-{len(parsed)+1:03d}"
        token = reg_id

        parsed.append({
            'registration_id': reg_id,
            'team_id': f"T-{len(parsed)+1:03d}",
            'team_name': team_name,
            'participant_name': name,
            'participant_email': email if email.lower() != 'nan' else '',
            'college_name': branch,
            'qr_token': token,
            'registration_status': 'Confirmed',
            'attendance_status': 'Pending'
        })

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    url = f"{SUPABASE_URL}/rest/v1/Buildora2k26"

    print("Deleting existing records from Supabase...")
    requests.delete(f"{url}?qr_token=not.is.null", headers=headers)

    print(f"Uploading {len(parsed)} students from Excel to Supabase in batches...")
    for chunk in [parsed[x:x+50] for x in range(0, len(parsed), 50)]:
        res = requests.post(url, headers=headers, json=chunk)
        if res.status_code not in [200, 201]:
            print(f"Batch upload failed with status {res.status_code}: {res.text}")

    print(f"Successfully pushed all {len(parsed)} students from Excel to Supabase!")

if __name__ == "__main__":
    import_excel_and_sync()
