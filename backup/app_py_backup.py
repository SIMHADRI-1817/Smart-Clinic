# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
 
app = Flask(__name__)
app.secret_key = "dev_secret_for_flash"  # only for development
 
DB = 'clinic.db'
 
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
 
@app.route('/')
def home():
    return render_template('index.html')
 
# Booking page (GET shows form, POST saves)
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        patient = request.form.get('patient_name', '').strip()
        doctor = request.form.get('doctor_name', '').strip()
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
        if not (patient and doctor and date and time):
            flash("All fields are required.", "error")
            return redirect(url_for('booking'))
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO appointments (patient_name, doctor_name, date, time) VALUES (?,?,?,?)',
            (patient, doctor, date, time)
        )
        conn.commit()
        conn.close()
        flash("Appointment booked successfully.", "success")
        return redirect(url_for('appointments'))
    return render_template('booking.html')
 
# Patient view: show all appointments (read-only)
@app.route('/appointments')
def appointments():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM appointments ORDER BY date, time').fetchall()
    conn.close()
    return render_template('appointments.html', appointments=rows)
 
# Receptionist dashboard: check-in, cancel
@app.route('/reception')
def reception():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM appointments ORDER BY date, time').fetchall()
    conn.close()
    return render_template('reception.html', appointments=rows)
 
@app.route('/checkin/<int:appointment_id>')
def checkin(appointment_id):
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status='checked_in' WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()
    flash("Patient checked in.", "success")
    return redirect(url_for('reception'))
 
@app.route('/cancel/<int:appointment_id>')
def cancel(appointment_id):
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()
    flash("Appointment cancelled.", "info")
    return redirect(url_for('reception'))
 
# Admin dashboard - simple stats
@app.route('/admin')
def admin():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
    today = datetime.now().date().isoformat()
    today_count = conn.execute('SELECT COUNT(*) FROM appointments WHERE date=?', (today,)).fetchone()[0]
    checked_in = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='checked_in'").fetchone()[0]
    cancelled = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='cancelled'").fetchone()[0]
    conn.close()
    stats = {
        'total': total,
        'today': today_count,
        'checked_in': checked_in,
        'cancelled': cancelled
    }
    return render_template('admin.html', stats=stats)
 
if __name__ == '__main__':
    app.run(debug=True)
 