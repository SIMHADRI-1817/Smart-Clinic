from flask import Flask, render_template, request, redirect, url_for, flash, Response, session, jsonify
import sqlite3
from datetime import datetime
import csv
from io import StringIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
 
app = Flask(__name__)
app.secret_key = "dev_secret_for_flash"  # use a strong key for production
DB = 'clinic.db'
 
# -------------------------
# Database connection helper
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
 
# -------------------------
# Authentication helpers
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function
 
def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            role = session.get('role')
            if role not in allowed_roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
 
def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, full_name, role FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    return user
 
# -------------------------
# Authentication routes
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role', 'patient').strip()
        if role not in ('patient', 'reception', 'admin'):
             flash("Invalid role selected.", "error")
             return redirect(url_for('register'))

        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if role == 'patient' and not session.get('role') in ('admin', 'reception'):
            flash("New patient registration is handled on the Login page.", "info")
            return redirect(url_for('login'))
 
        if not (username and password):
            flash("Username and password required.", "error")
            return redirect(url_for('register'))
 
        hashed = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, full_name, email, password, role) VALUES (?,?,?,?,?)',
                (username, full_name, email, hashed, role)
            )
            conn.commit()
            flash(f"Registration for user '{username}' successful. Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "error")
        finally:
            conn.close()
            
    if session.get('role') not in ('admin', 'reception'):
        return redirect(url_for('home')) 
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'login':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
 
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            conn.close()
 
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                flash("Logged in successfully.", "success")
 
                if user['role'] == 'admin':
                    return redirect(url_for('admin'))
                elif user['role'] == 'reception':
                    return redirect(url_for('reception'))
                else:
                    return redirect(url_for('patient_dashboard'))
            else:
                flash("Invalid username or password.", "error")
                return redirect(url_for('login'))
        
        elif action == 'signup':
            username = request.form.get('username', '').strip()
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            role = 'patient'
 
            if not (username and password and full_name and email):
                flash("All fields are required for sign up.", "error")
                return redirect(url_for('login'))
 
            hashed = generate_password_hash(password)
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, full_name, email, password, role) VALUES (?,?,?,?,?)',
                    (username, full_name, email, hashed, role)
                )
                conn.commit()
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username or email already exists.", "error")
            finally:
                conn.close()

        else:
            flash("Invalid action.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')
 
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))
 
# -------------------------
# Home route
# -------------------------
@app.route('/')
def home():
    user = get_current_user()
    return render_template('index.html', user=user)

# -------------------------
# Contact Routes
# -------------------------
@app.route('/contact')
def contact():
    user = get_current_user()
    return render_template('contact.html', user=user)

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    print(f"📩 Message from {name} ({email}): {message}")
    flash("Your message has been sent successfully!", "success")
    return redirect(url_for('contact'))

# -------------------------
# Booking route
# -------------------------
@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    conn = get_db_connection()
    doctors = conn.execute(
        "SELECT full_name, specialization FROM users WHERE role='doctor' ORDER BY full_name"
    ).fetchall()
 
    if request.method == 'POST':
        patient = session.get('full_name') or "Unknown"
        doctor = request.form.get('doctor_name', '').strip()
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
        
        booked = conn.execute(
            "SELECT id FROM appointments WHERE doctor_name=? AND date=? AND time=? AND status IN ('pending', 'checked_in')",
            (doctor, date, time)
        ).fetchone()
        
        if booked:
            flash("This specific time slot has just been booked. Please choose another time.", "error")
            conn.close()
            return redirect(url_for('booking'))
 
        if not (patient and doctor and date and time):
            flash("All fields are required.", "error")
            conn.close()
            return redirect(url_for('booking'))
 
        conn.execute(
            "INSERT INTO appointments (patient_name, doctor_name, date, time, status) VALUES (?,?,?,?,?)",
            (patient, doctor, date, time, 'pending')
        )
        conn.commit()
        conn.close()
 
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('patient_dashboard'))
 
    conn.close()
    all_times = [
        '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
    ]
    return render_template('booking.html', doctors=doctors, all_times=all_times)

# -------------------------
# Doctor Availability API
# -------------------------
@app.route('/api/doctor_availability', methods=['GET'])
@login_required
def doctor_availability():
    doctor_name = request.args.get('doctor')
    date = request.args.get('date')
    
    if not (doctor_name and date):
        return jsonify({'error': 'Doctor and date parameters are required.'}), 400
    
    conn = get_db_connection()
    booked_slots = conn.execute(
        "SELECT time FROM appointments WHERE doctor_name=? AND date=? AND status IN ('pending', 'checked_in') ORDER BY time", 
        (doctor_name, date)
    ).fetchall()
    conn.close()
    
    occupied_times = [slot['time'] for slot in booked_slots]
    standard_times = [
        '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
    ]
    available_times = [time for time in standard_times if time not in occupied_times]
    
    return jsonify({'available_times': available_times})

# -------------------------
# Patient Dashboard
# -------------------------
@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    conn = get_db_connection()
    appts = conn.execute(
        'SELECT * FROM appointments WHERE patient_name=? ORDER BY date, time',
        (session['full_name'],)
    ).fetchall()
    conn.close()
    user = get_current_user()
    return render_template('patient_dashboard.html', appointments=appts, user=user)

# -------------------------
# Edit Appointment
# -------------------------
@app.route('/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    conn = get_db_connection()
    appt = conn.execute('SELECT * FROM appointments WHERE id=?', (appointment_id,)).fetchone()
 
    if appt is None:
        conn.close()
        flash("Appointment not found.", "error")
        return redirect(url_for('patient_dashboard'))
 
    if appt['patient_name'] != session.get('full_name') and session.get('role') == 'patient':
        conn.close()
        flash("You can only edit your own appointments.", "error")
        return redirect(url_for('patient_dashboard'))

    doctors = conn.execute("SELECT full_name, specialization FROM users WHERE role='doctor' ORDER BY full_name").fetchall()
    all_times = [
        '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
    ]
    
    if request.method == 'POST':
        doctor = request.form.get('doctor_name', '').strip()
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
 
        if not (doctor and date and time):
            flash("All fields are required.", "error")
            conn.close()
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))

        conflict = conn.execute(
            "SELECT id FROM appointments WHERE doctor_name=? AND date=? AND time=? AND status IN ('pending', 'checked_in') AND id!=?",
            (doctor, date, time, appointment_id)
        ).fetchone()

        if conflict:
            conn.close()
            flash("The selected time slot is already booked. Please choose another time.", "error")
            return redirect(url_for('edit_appointment', appointment_id=appointment_id))
 
        conn.execute(
            "UPDATE appointments SET doctor_name=?, date=?, time=? WHERE id=?",
            (doctor, date, time, appointment_id)
        )
        conn.commit()
        conn.close()
        flash("Appointment updated successfully.", "success")
        return redirect(url_for('patient_dashboard'))
 
    conn.close()
    return render_template('edit_appointment.html', appt=appt, doctors=doctors, all_times=all_times)

# -------------------------
# Reception Dashboard
# -------------------------
@app.route('/reception')
@login_required
@role_required('reception', 'admin')
def reception():
    date = request.args.get('date', '').strip()
    doctor = request.args.get('doctor', '').strip()
    conn = get_db_connection()
 
    if date and doctor:
        rows = conn.execute(
            "SELECT * FROM appointments WHERE date=? AND doctor_name LIKE ? ORDER BY time",
            (date, f'%{doctor}%')
        ).fetchall()
    elif date:
        rows = conn.execute(
            "SELECT * FROM appointments WHERE date=? ORDER BY time", (date,)
        ).fetchall()
    elif doctor:
        rows = conn.execute(
            "SELECT * FROM appointments WHERE doctor_name LIKE ? ORDER BY date, time",
            (f'%{doctor}%',)
        ).fetchall()
    else:
        today = datetime.now().date().isoformat()
        rows = conn.execute("SELECT * FROM appointments WHERE date=? ORDER BY time", (today,)).fetchall()
        
    conn.close()
    user = get_current_user()
    return render_template('reception.html', appointments=rows, user=user)
 
@app.route('/checkin/<int:appointment_id>')
@login_required
@role_required('reception', 'admin')
def checkin(appointment_id):
    conn = get_db_connection()
    appt = conn.execute("SELECT doctor_name, date FROM appointments WHERE id=?", (appointment_id,)).fetchone()
    if appt:
        max_queue = conn.execute(
            "SELECT MAX(queue_number) FROM appointments WHERE doctor_name=? AND date=?",
            (appt['doctor_name'], appt['date'])
        ).fetchone()[0]
        
        new_queue = (max_queue or 0) + 1
        
        conn.execute(
            "UPDATE appointments SET status='checked_in', queue_number=? WHERE id=?", 
            (new_queue, appointment_id)
        )
        conn.commit()
        flash(f"Patient checked in successfully. Queue Number: {new_queue}", "success")
    else:
        flash("Appointment not found.", "error")

    conn.close()
    return redirect(url_for('reception'))
 
@app.route('/cancel/<int:appointment_id>')
@login_required
@role_required('reception', 'admin')
def cancel(appointment_id):
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()
    flash("Appointment cancelled.", "info")
    return redirect(url_for('reception'))
 
# -------------------------
# Admin Dashboard
# -------------------------
@app.route('/admin')
@login_required
@role_required('admin')
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
    user = get_current_user()
    return render_template('admin.html', stats=stats, todays=todays, user=user)
 
# -------------------------
# Export CSV (Admin Only)
# -------------------------
@app.route('/export')
@login_required
@role_required('admin')
def export_csv():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
    conn.close()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'patient_name', 'doctor_name', 'date', 'time', 'status'])
    for r in rows:
        cw.writerow([r['id'], r['patient_name'], r['doctor_name'], r['date'], r['time'], r['status']])
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=appointments.csv"})
 
# -------------------------
# Run Flask
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
