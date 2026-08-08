import os
import sys
import json
import pypdf
import requests

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "student details", "Hackethon final list (1).pdf"))

def parse_pdf_and_sync():
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return

    reader = pypdf.PdfReader(pdf_path)

    p1 = [l.strip() for l in reader.pages[0].extract_text().split('\n') if l.strip() and l.strip() != 'Team Name Team Member Name']
    p2 = [l.strip() for l in reader.pages[1].extract_text().split('\n') if l.strip()]
    p3 = [l.strip() for l in reader.pages[2].extract_text().split('\n') if l.strip()]
    name_lines = p1 + p2 + p3

    p4 = [l.strip() for l in reader.pages[3].extract_text().split('\n') if l.strip() and l.strip() != 'Number of Team Members Year & Branch']
    p5 = [l.strip() for l in reader.pages[4].extract_text().split('\n') if l.strip()]
    p6 = [l.strip() for l in reader.pages[5].extract_text().split('\n') if l.strip()]
    branch_lines = p4 + p5 + p6

    p7 = [l.strip() for l in reader.pages[6].extract_text().split('\n') if l.strip() and l.strip() != 'Email Address']
    p8 = [l.strip() for l in reader.pages[7].extract_text().split('\n') if l.strip()]
    p9 = [l.strip() for l in reader.pages[8].extract_text().split('\n') if l.strip()]
    email_lines = p7 + p8 + p9

    parsed = []
    for i in range(len(name_lines)):
        line = name_lines[i]
        br = branch_lines[i]
        em = email_lines[i]
        
        parts = line.split()
        if len(parts) >= 3 and parts[0] == parts[1]:
            team_name = parts[0]
            member_name = ' '.join(parts[2:])
        elif len(parts) >= 2:
            team_name = parts[0]
            member_name = ' '.join(parts[1:])
        else:
            team_name = 'General'
            member_name = line

        reg_id = f'BUILD26-{i+1:03d}'
        token = reg_id
        
        parsed.append({
            'registration_id': reg_id,
            'team_id': f'T-{i+1:03d}',
            'team_name': team_name,
            'participant_name': member_name,
            'participant_email': em if em != 'N/A' else '',
            'college_name': br,
            'qr_token': token,
            'registration_status': 'Confirmed',
            'attendance_status': 'Pending'
        })

    from config import SUPABASE_KEY, SUPABASE_URL
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    url = f'{SUPABASE_URL}/rest/v1/Buildora2k26'

    print("Deleting existing records...")
    requests.delete(f'{url}?qr_token=not.is.null', headers=headers)

    print(f"Uploading {len(parsed)} students to Supabase...")
    res = requests.post(url, headers=headers, json=parsed)
    if res.status_code in [200, 201]:
        print(f"Successfully uploaded {len(parsed)} students from Hackethon final list (1).pdf to Supabase!")
    else:
        print(f"Upload returned status code {res.status_code}: {res.text}")

if __name__ == "__main__":
    parse_pdf_and_sync()
