# init_db.py
import sqlite3
from werkzeug.security import generate_password_hash
 
def init_db():
    conn = sqlite3.connect('clinic.db')
    cur = conn.cursor()
 
    # appointments table (keeps existing schema)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        doctor_name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'booked'
    )
    ''')
 
    # users table: role can be 'admin', 'reception', or 'patient'
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'patient',
        full_name TEXT
    )
    ''')
 
    # create a default admin user if not exists
    # NOTE: change password after first login in production
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    admin_password = 'admin123'  # you can change this before running
 
    cur.execute("SELECT id FROM users WHERE username=?", (admin_username,))
    if cur.fetchone() is None:
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(admin_password)
        cur.execute("INSERT INTO users (username, email, password, role, full_name) VALUES (?,?,?,?,?)",
                    (admin_username, admin_email, hashed, 'admin', 'Site Admin'))
        print("Created default admin user (username: admin, password: admin123)")
 
    conn.commit()
    conn.close()
    print("Database initialized (clinic.db)")
 
if __name__ == "__main__":
    init_db()