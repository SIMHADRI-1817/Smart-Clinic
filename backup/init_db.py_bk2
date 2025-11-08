# init_db.py
import sqlite3
from werkzeug.security import generate_password_hash
 
# Connect (or create) the database file
conn = sqlite3.connect("clinic.db")
 
# ---------------------------
# 1️⃣ Create the users table
# ---------------------------
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('patient', 'reception', 'admin')) NOT NULL,
    full_name TEXT
)
""")
 
# -------------------------------
# 2️⃣ Create the appointments table
# -------------------------------
conn.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
)
""")
 
# -----------------------------------
# 3️⃣ Create default user accounts
# -----------------------------------
 
# Admin account
admin_pass = generate_password_hash("admin123")
conn.execute("""
INSERT OR IGNORE INTO users (username, email, password, role, full_name)
VALUES ('admin', 'admin@clinic.com', ?, 'admin', 'Admin User')
""", (admin_pass,))
 
# Reception account
reception_pass = generate_password_hash("reception123")
conn.execute("""
INSERT OR IGNORE INTO users (username, email, password, role, full_name)
VALUES ('reception', 'reception@clinic.com', ?, 'reception', 'Reception Staff')
""", (reception_pass,))
 
# Patient account
patient_pass = generate_password_hash("patient123")
conn.execute("""
INSERT OR IGNORE INTO users (username, email, password, role, full_name)
VALUES ('patient', 'patient@clinic.com', ?, 'patient', 'John Doe')
""", (patient_pass,))
 
# Save everything and close the connection
conn.commit()
conn.close()
 
print("✅ Database initialized successfully!")
print("➡ Default users created:")
print("   Admin: admin / admin123")
print("   Reception: reception / reception123")
print("   Patient: patient / patient123")