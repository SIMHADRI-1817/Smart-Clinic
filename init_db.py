import sqlite3
from werkzeug.security import generate_password_hash
 
conn = sqlite3.connect('clinic.db')
 
# Drop old tables if you want a fresh start (optional)
conn.execute("DROP TABLE IF EXISTS appointments")
conn.execute("DROP TABLE IF EXISTS users")
 
# Create appointments table
conn.execute('''
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    queue_number INTEGER
)
''')
 
# Create users table with specialization
conn.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('patient','reception','admin','doctor')) NOT NULL,
    specialization TEXT
)
''')
 
# Add sample doctors
doctors = [
    ('dr_Ashish', 'Dr. Ashish', 'ashish@clinic.com', generate_password_hash('12345'), 'doctor', 'Cardiologist'),
    ('dr_Neha', 'Dr. Neha Sharma', 'neha@clinic.com', generate_password_hash('12345'), 'doctor', 'Dermatologist'),
    ('dr_Ravi', 'Dr. Ravi Teja', 'ravi@clinic.com', generate_password_hash('12345'), 'doctor', 'Pediatrician')
]
 
conn.executemany('INSERT INTO users (username, full_name, email, password, role, specialization) VALUES (?, ?, ?, ?, ?, ?)', doctors)
 
# Add one sample admin and receptionist
conn.execute("INSERT INTO users (username, full_name, email, password, role) VALUES (?, ?, ?, ?, ?)",
             ('admin', 'Admin User', 'admin@clinic.com', generate_password_hash('admin123'), 'admin'))
conn.execute("INSERT INTO users (username, full_name, email, password, role) VALUES (?, ?, ?, ?, ?)",
             ('reception', 'Reception Staff', 'reception@clinic.com', generate_password_hash('reception123'), 'reception'))
 
conn.commit()
conn.close()
print("✅ Database initialized successfully with sample data.")