QR-Based Farewell Entry Verification System
Goal Description
Create a complete, beginner‑friendly project that allows volunteers to open a web page, scan a student’s QR code, and instantly see whether the entry is allowed, already used, or invalid. The system consists of:

Frontend (HTML, CSS, Bootstrap, JavaScript) with a QR scanner using html5-qrcode.
Backend (Flask) exposing a /verify POST endpoint that checks a Supabase PostgreSQL table.
Database (Supabase) with a passes table storing student details and a unique token.
Scripts for bulk QR generation from a CSV file.
Deployment ready for Netlify (frontend) and Render (backend).
The project will be organized into clear folders:

project_root/
├─ backend/
│   ├─ app.py
│   ├─ requirements.txt
│   └─ .render.yaml
├─ frontend/
│   ├─ index.html
│   ├─ style.css
│   └─ netlify.toml
├─ scripts/
│   └─ generate_qr.py
└─ database/
    └─ schema.sql
User Review Required
IMPORTANT

Please review the following items and provide any missing information or preferences:

Supabase credentials: SUPABASE_URL and SUPABASE_ANON_KEY. These will be placed in a .env file for the backend.
Deployment preferences: Do you want the provided Render and Netlify configuration files as‑is, or do you have custom domain / environment variable requirements?
QR generation script: Do you prefer the QR images saved as PNG files in a qr_codes/ folder, or should they be uploaded to Supabase storage?
Sample data: Provide a small CSV example (or confirm we can create a dummy one) for bulk QR generation.
UI color scheme: Any specific colors or branding for the scanner page? (We will use a vibrant, modern palette by default.)
Proposed Changes
Backend (backend/)
[NEW] backend/app.py – Flask app with /verify POST endpoint. Uses supabase-py to query the passes table, updates used flag, and returns JSON status.
[NEW] backend/requirements.txt – Lists Flask, supabase, python-dotenv.
[NEW] backend/.env – Environment file (not committed) containing SUPABASE_URL and SUPABASE_ANON_KEY.
[NEW] backend/.render.yaml – Render service definition for Python.
Frontend (frontend/)
[NEW] frontend/index.html – Main scanner page using Bootstrap and html5-qrcode.
[NEW] frontend/style.css – Custom styling with a modern color palette, responsive layout, and status screens (green, yellow, red).
[NEW] frontend/netlify.toml – Netlify configuration for static site deployment.
Scripts (scripts/)
[NEW] scripts/generate_qr.py – Reads a CSV (student_name,roll_number) and generates a UUID token for each row, inserts records into Supabase via its REST API, and creates QR PNG files using qrcode library.
[NEW] scripts/requirements.txt – Lists qrcode, pandas, supabase-py.
Database (database/)
[NEW] database/schema.sql – SQL to create the passes table with fields id UUID PRIMARY KEY, student_name TEXT, roll_number TEXT, token TEXT UNIQUE, used BOOLEAN DEFAULT FALSE.
Documentation (README.md)
[NEW] README.md – Step‑by‑step guide covering:
Setting up Supabase and obtaining credentials.
Running the backend locally (pip install -r requirements.txt && python app.py).
Deploying backend to Render.
Deploying frontend to Netlify.
Generating QR codes from a CSV.
Testing the system.
Open Questions
Supabase credentials – Please provide the URL and anon key, or confirm we should leave placeholders.
Deployment details – Any custom domain or environment variable naming conventions for Render/Netlify?
QR storage – Save locally or upload to Supabase storage?
Sample CSV format – Columns order and delimiter (default: student_name,roll_number).
UI branding – Preferred primary/secondary colors?
Verification Plan
Automated Tests
Use curl to POST sample tokens to the backend and verify JSON responses for each case (invalid, used, valid).
Run the QR generation script on a small CSV and confirm rows are inserted into Supabase and PNG files are created.
Manual Verification
Deploy the frontend to Netlify (or run locally via npx serve).
Open the scanner page on a mobile browser, scan a generated QR code, and observe the colored status screen.
Test network failure by disabling internet and confirming the UI shows an error message.
Once the above questions are answered, I will proceed to create the project files and scripts.