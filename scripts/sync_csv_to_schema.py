import random
import uuid

first_names = ["Arjun", "Aditi", "Rohan", "Sanya", "Vikram", "Neha", "Aarav", "Isha", "Karan", "Pooja", 
               "Rahul", "Anjali", "Varun", "Riya", "Siddharth", "Kavya", "Amit", "Sneha", "Pranav", "Tanvi"]
last_names = ["Sharma", "Verma", "Gupta", "Malhotra", "Kapoor", "Singh", "Yadav", "Patel", "Reddy", "Nair",
              "Choudhury", "Das", "Mishra", "Joshi", "Kulkarni", "Deshmukh", "Pillai", "Iyer", "Rao", "Bose"]
branches = ["Computer Science", "Mechanical Engineering", "Information Technology", "Civil Engineering", 
            "Electrical Engineering", "Electronics", "Chemical Engineering", "Biotechnology"]

rows = []
rows.append("token,student_name,Status,Branch")

for i in range(1000):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    branch = random.choice(branches)
    token = str(uuid.uuid4())[:8]
    status = "Valid"
    rows.append(f"{token},{name},{status},{branch}")

with open(r"c:\Users\pc\OneDrive\Desktop\New folder (8)\farewell2k26\backend\routes\student.csv", "w") as f:
    f.write("\n".join(rows))

print("Successfully updated student.csv with schema: token,student_name,Status,Branch")
