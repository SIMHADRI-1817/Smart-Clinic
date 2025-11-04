# init_db.py
import sqlite3
 
def init_db():
    conn = sqlite3.connect('clinic.db')
    cur = conn.cursor()
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
    conn.commit()
    conn.close()
    print("Database initialized (clinic.db)")
 
if __name__ == "__main__":
    init_db()