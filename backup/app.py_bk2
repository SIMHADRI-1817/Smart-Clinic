from flask import Flask, render_template, request, redirect, url_for, flash, Response, session
import sqlite3
from datetime import datetime
import csv
from io import StringIO
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "dev_secret_for_flash"  # change in production

DB = 'clinic.db'

# -------------------------
# Database helpers
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def table_has_column(table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    conn = get_db_connection()
    try:
        info = conn.execute(f"PRAGMA table_info({table})").fetchall()
        cols = [r['name'] for r in info]
        return column in cols
    finally:
        conn.close()


def ensure_schema_and_admin():
    """Ensure DB tables exist and default admin user is created."""
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'patient',
                full_name TEXT
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT,
                doctor_name TEXT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'scheduled'
            )
        ''')

        # Add user_id column if missing
        if not table_has_column('appointments', 'user_id'):
            try:
                conn.execute("ALTER TABLE appointments ADD COLUMN user_id INTEGER")
            except sqlite3.OperationalError:
                pass

        # Create default admin user
        existing_admin = conn.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not existing_admin:
            hashed = generate_password_hash('admin123')
            conn.execute(
                'INSERT INTO users (username, email, password, role, full_name) VALUES (?,?,?,?,?)',
                ('admin', 'admin@example.com', hashed, 'admin', 'Administrator')
            )
            conn.commit()
            print("✅ Default admin created — username: admin | password: admin123")

        conn.commit()
    finally:
        conn.close()


# Create DB + admin if missing
if not os.path.exists(DB):
    open(DB, 'a').close()
ensure_schema_and_admin()


# -------------------------
# Auth helpers
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
    try:
        user = conn.execute(
            'SELECT id, username, full_name, role FROM users WHERE id=?', (uid,)
        ).fetchone()
        return user
    finally:
        conn.close()


# -------------------------
# Auth routes
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = 'patient'  # Default for all new users

        if not (username and password):
            flash("Username and password required.", "error")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password, role, full_name) VALUES (?,?,?,?,?)',
                (username, email, hashed, role, full_name)
            )
            conn.commit()
            conn.close()
            # Redirect to welcome screen after success
            return redirect(url_for('welcome', name=full_name))
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "error")
            conn.close()
            return redirect(url_for('register'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash("Logged in successfully!", "success")

            # redirect by role
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            elif user['role'] == 'reception':
                return redirect(url_for('reception'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))
@app.route('/welcome')
def welcome():
    name = request.args.get('name', 'New User')
    return render_template('welcome.html', name=name)



# -------------------------
# Core pages
# -------------------------
@app.route('/')
def home():
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/booking', methods=['GET', 'POST'])
@login_required
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
        try:
            if table_has_column('appointments', 'user_id'):
                conn.execute(
                    'INSERT INTO appointments (patient_name, doctor_name, date, time, status, user_id) VALUES (?,?,?,?,?,?)',
                    (patient, doctor, date, time, 'scheduled', session.get('user_id'))
                )
            else:
                conn.execute(
                    'INSERT INTO appointments (patient_name, doctor_name, date, time, status) VALUES (?,?,?,?,?)',
                    (patient, doctor, date, time, 'scheduled')
                )
            conn.commit()
        finally:
            conn.close()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('appointments'))

    return render_template('booking.html')


@app.route('/appointments')
@login_required
def appointments():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM appointments ORDER BY date, time').fetchall()
    finally:
        conn.close()
    return render_template('appointments.html', appointments=rows)


@app.route('/patient_dashboard')
@login_required
def patient_dashboard():
    q = request.args.get('q', '').strip()
    conn = get_db_connection()
    try:
        if q:
            rows = conn.execute(
                "SELECT * FROM appointments WHERE patient_name LIKE ? ORDER BY date, time",
                ('%' + q + '%',)
            ).fetchall()
        else:
            rows = conn.execute('SELECT * FROM appointments ORDER BY date, time').fetchall()
    finally:
        conn.close()
    return render_template('patient_dashboard.html', appointments=rows)


# -------------------------
# Reception dashboard
# -------------------------
@app.route('/reception')
@login_required
@role_required('reception', 'admin')
def reception():
    date = request.args.get('date', '').strip()
    doctor = request.args.get('doctor', '').strip()

    conn = get_db_connection()
    query = "SELECT * FROM appointments"
    params = []
    filters = []

    if date:
        filters.append("date=?")
        params.append(date)
    if doctor:
        filters.append("doctor_name LIKE ?")
        params.append('%' + doctor + '%')

    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY date, time"

    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    return render_template('reception.html', appointments=rows)


# -------------------------
# Check-in & Cancel
# -------------------------
@app.route('/checkin/<int:appointment_id>')
@login_required
@role_required('reception', 'admin')
def checkin(appointment_id):
    conn = get_db_connection()
    try:
        conn.execute("UPDATE appointments SET status='checked_in' WHERE id=?", (appointment_id,))
        conn.commit()
    finally:
        conn.close()
    flash("Patient checked in!", "success")
    return redirect(url_for('reception'))


@app.route('/cancel/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def cancel_appointment(appointment_id):
    conn = get_db_connection()
    try:
        appt = conn.execute('SELECT * FROM appointments WHERE id=?', (appointment_id,)).fetchone()
        if not appt:
            flash("Appointment not found.", "error")
            return redirect(url_for('appointments'))

        role = session.get('role')
        user_id = session.get('user_id')
        full_name = session.get('full_name')

        # Admin/Reception can cancel any
        if role in ('admin', 'reception'):
            conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appointment_id,))
            conn.commit()
            flash("Appointment cancelled.", "info")
            return redirect(url_for('reception'))

        # Patients can cancel only their own
        can_cancel = False
        if table_has_column('appointments', 'user_id'):
            if appt['user_id'] == user_id:
                can_cancel = True
        else:
            if appt['patient_name'] == full_name:
                can_cancel = True

        if can_cancel:
            conn.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appointment_id,))
            conn.commit()
            flash("Your appointment has been cancelled.", "info")
        else:
            flash("You don't have permission to cancel this.", "error")
    finally:
        conn.close()
    return redirect(url_for('appointments'))


# -------------------------
# Admin dashboard & export
# -------------------------
@app.route('/admin')
@login_required
@role_required('admin')
def admin():
    conn = get_db_connection()
    try:
        total = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]
        today = datetime.now().date().isoformat()
        today_count = conn.execute('SELECT COUNT(*) FROM appointments WHERE date=?', (today,)).fetchone()[0]
        checked_in = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='checked_in'").fetchone()[0]
        cancelled = conn.execute("SELECT COUNT(*) FROM appointments WHERE status='cancelled'").fetchone()[0]
        todays = conn.execute("SELECT * FROM appointments WHERE date=? ORDER BY time", (today,)).fetchall()
    finally:
        conn.close()

    stats = {'total': total, 'today': today_count, 'checked_in': checked_in, 'cancelled': cancelled}
    return render_template('admin.html', stats=stats, todays=todays)


@app.route('/export')
@login_required
@role_required('admin')
def export_csv():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM appointments ORDER BY date, time").fetchall()
    finally:
        conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'patient_name', 'doctor_name', 'date', 'time', 'status'])
    for r in rows:
        cw.writerow([r['id'], r['patient_name'], r['doctor_name'], r['date'], r['time'], r['status']])

    output = si.getvalue()
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=appointments.csv"})


# -------------------------
# Run app
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
