import csv
import sys
import os

# Add backend to path so we can import db
sys.path.append(os.path.join(os.getcwd(), "backend"))
from db import db

csv_paths = [
    os.path.join(os.getcwd(), "scripts", "students.csv"),
    os.path.join(os.getcwd(), "backend", "routes", "student.csv"),
    os.path.join(os.getcwd(), "backend", "routes", "students.csv")
]

csv_path = None
for path in csv_paths:
    if os.path.exists(path):
        csv_path = path
        break

def push_data():
    from scripts.import_excel_to_supabase import import_excel_and_sync
    import_excel_and_sync()

if __name__ == "__main__":
    push_data()
