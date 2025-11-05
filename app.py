# app.py (complete updated file for Week 2)
from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
from datetime import datetime
import csv
from io import StringIO
 
app = Flask(__name__)
app.secret_key = "dev_secret_for_flash"  # development only
 
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
 
# Patient dashboard (search & list)
@app.route('/patient_dashboard', methods=['GET'])
def patient_dashboard():
    q = request.args.get('q', '').strip()
    conn = get_db_connection()
    if q:
        rows = conn.execute("SELECT * FROM appointments WHERE patient_name LIKE ? ORDER BY date, time", ('%'+q+'%',)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
    conn.close()
    return render_template('patient_dashboard.html', appointments=rows)
 
# Edit appointment (simple inline form)
@app.route('/edit/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    conn = get_db_connection()
    appt = conn.execute('SELECT * FROM appointments WHERE id=?', (appointment_id,)).fetchone()
    if appt is None:
        conn.close()
        flash("Appointment not found.", "error")
        return redirect(url_for('patient_dashboard'))
    if request.method == 'POST':
        doctor = request.form.get('doctor_name','').strip()
        date = request.form.get('date','').strip()
        time = request.form.get('time','').strip()
        if not (doctor and date and time):
            flash("All fields are required.", "error")
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))
        conn.execute("UPDATE appointments SET doctor_name=?, date=?, time=? WHERE id=?", (doctor, date, time, appointment_id))
        conn.commit()
        conn.close()
        flash("Appointment updated.", "success")
        return redirect(url_for('patient_dashboard'))
    # GET -> show simple edit form (inline)
    form_html = f'''
    <!doctype html>
    <html><head><meta charset="utf-8"><title>Edit Appointment</title></head><body>
    <h3>Edit Appointment #{appt["id"]}</h3>
    <form method="post">
      Doctor: <input name="doctor_name" value="{appt['doctor_name']}" required><br>
      Date: <input name="date" type="date" value="{appt['date']}" required><br>
      Time: <input name="time" type="time" value="{appt['time']}" required><br>
      <button type="submit">Save</button>
    </form>
    <p><a href="{url_for('patient_dashboard')}">Back</a></p>
    </body></html>
    '''
    conn.close()
    return form_html
 
# Receptionist dashboard with filters
@app.route('/reception')
def reception():
    date = request.args.get('date','').strip()
    doctor = request.args.get('doctor','').strip()
    conn = get_db_connection()
    if date and doctor:
        rows = conn.execute("SELECT * FROM appointments WHERE date=? AND doctor_name LIKE ? ORDER BY time", (date, '%'+doctor+'%')).fetchall()
    elif date:
        rows = conn.execute("SELECT * FROM appointments WHERE date=? ORDER BY time", (date,)).fetchall()
    elif doctor:
        rows = conn.execute("SELECT * FROM appointments WHERE doctor_name LIKE ? ORDER BY date, time", ('%'+doctor+'%',)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
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
 
# Admin dashboard + today's list
@app.route('/admin')
def admin():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
    today = datetime.now().date().isoformat()
    today_count = conn.execute('SELECT COUNT(*) FROM appointments WHERE date=?', (today,)).fetchone()[0]
    checked_in = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='checked_in'").fetchone()[0]
    cancelled = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='cancelled'").fetchone()[0]
    todays = conn.execute("SELECT * FROM appointments WHERE date=? ORDER BY time", (today,)).fetchall()
    conn.close()
    stats = {'total': total, 'today': today_count, 'checked_in': checked_in, 'cancelled': cancelled}
    return render_template('admin.html', stats=stats, todays=todays)
 
# CSV export
@app.route('/export')
def export_csv():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
    conn.close()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id','patient_name','doctor_name','date','time','status'])
    for r in rows:
        cw.writerow([r['id'], r['patient_name'], r['doctor_name'], r['date'], r['time'], r['status']])
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=appointments.csv"})
 
if __name__ == '__main__':
    app.run(debug=True)