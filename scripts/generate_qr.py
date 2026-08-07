import qrcode
import csv
import uuid
import requests

SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-key"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

with open("students.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)

    for row in reader:
        token = str(uuid.uuid4())

        data = {
            "student_name": row["name"],
            "roll_number": row["roll_number"],
            "token": token,
            "paid": True,
            "used": False
        }

        requests.post(f"{SUPABASE_URL}/rest/v1/passes", json=data, headers=headers)

        img = qrcode.make(token)
        img.save(f"qrcodes/{row['roll_number']}.png")
        