from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "attendance123"


# ==========================
# DATABASE CONNECTION
# ==========================

def get_db():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# CREATE TABLES
# ==========================

conn = get_db()

conn.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    att_date TEXT,
    status TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS admin(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.execute("""
INSERT OR IGNORE INTO admin
(id, username, password)
VALUES
(1, 'admin', 'admin123')
""")

conn.commit()


# ==========================
# HOME PAGE
# ==========================

@app.route('/')
def home():
    return render_template('index.html')


# ==========================
# REGISTER STUDENT
# ==========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']

        conn = get_db()

        conn.execute(
            """
            INSERT INTO students(name,email)
            VALUES(?,?)
            """,
            (name, email)
        )

        conn.commit()

        return redirect('/students')

    return render_template('register.html')


# ==========================
# STUDENTS PAGE
# ==========================

@app.route('/students')
def students():

    conn = get_db()

    students_data = conn.execute(
        """
        SELECT *
        FROM students
        ORDER BY id DESC
        """
    ).fetchall()

    return render_template(
        'students.html',
        students=students_data
    )


# ==========================
# ATTENDANCE PAGE
# ==========================

@app.route('/attendance')
def attendance():

    conn = get_db()

    students_data = conn.execute(
        """
        SELECT *
        FROM students
        ORDER BY name
        """
    ).fetchall()

    return render_template(
        'attendance.html',
        students=students_data
    )


# ==========================
# MARK ATTENDANCE
# ==========================

@app.route('/mark/<int:id>')
def mark(id):

    conn = get_db()

    today = str(date.today())

    existing = conn.execute(
        """
        SELECT *
        FROM attendance
        WHERE student_id=?
        AND att_date=?
        """,
        (id, today)
    ).fetchone()

    if not existing:

        conn.execute(
            """
            INSERT INTO attendance
            (student_id,att_date,status)
            VALUES (?,?,?)
            """,
            (
                id,
                today,
                "Present"
            )
        )

        conn.commit()

    return redirect('/attendance')


# ==========================
# REPORTS PAGE
# ==========================

@app.route('/reports')
def reports():

    conn = get_db()

    report = conn.execute(
        """
        SELECT
            students.name,
            COUNT(attendance.id) AS total

        FROM students

        LEFT JOIN attendance
        ON students.id = attendance.student_id

        GROUP BY students.id

        ORDER BY total DESC
        """
    ).fetchall()

    return render_template(
        'reports.html',
        reports=report
    )


# ==========================
# ADMIN LOGIN
# ==========================

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = get_db()

        admin_user = conn.execute(
            """
            SELECT *
            FROM admin
            WHERE username=?
            AND password=?
            """,
            (username, password)
        ).fetchone()

        if admin_user:

            session['admin'] = username

            return redirect('/admin_dashboard')

    return render_template('admin_login.html')


# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin')

    conn = get_db()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance"
    ).fetchone()[0]

    selected_date = request.args.get('date')

    if selected_date:

        attendance_data = conn.execute(
            """
            SELECT students.name,
                   attendance.att_date,
                   attendance.status
            FROM attendance
            JOIN students
            ON students.id = attendance.student_id
            WHERE attendance.att_date=?
            ORDER BY attendance.att_date DESC
            """,
            (selected_date,)
        ).fetchall()

        present_today = conn.execute(
            """
            SELECT COUNT(DISTINCT student_id)
            FROM attendance
            WHERE att_date=?
            """,
            (selected_date,)
        ).fetchone()[0]

    else:

        attendance_data = conn.execute(
            """
            SELECT students.name,
                   attendance.att_date,
                   attendance.status
            FROM attendance
            JOIN students
            ON students.id = attendance.student_id
            ORDER BY attendance.att_date DESC
            """
        ).fetchall()

        present_today = conn.execute(
            """
            SELECT COUNT(DISTINCT student_id)
            FROM attendance
            """
        ).fetchone()[0]

    if present_today > total_students:
        present_today = total_students

    absent_today = total_students - present_today

    if total_students > 0:
        attendance_percentage = round(
            (present_today / total_students) * 100,
            2
        )
    else:
        attendance_percentage = 0

    students_data = conn.execute(
        """
        SELECT *
        FROM students
        ORDER BY id DESC
        """
    ).fetchall()

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_attendance=total_attendance,
        present_today=present_today,
        absent_today=absent_today,
        attendance_percentage=attendance_percentage,
        students=students_data,
        attendance=attendance_data
    )


# ==========================
# ALL ATTENDANCE
# ==========================

@app.route('/allattendance')
def allattendance():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT students.name,
               attendance.att_date,
               attendance.status
        FROM attendance
        JOIN students
        ON students.id = attendance.student_id
        ORDER BY attendance.att_date DESC
        """
    ).fetchall()

    result = ""

    for row in rows:
        result += f"{row['name']} | {row['att_date']} | {row['status']}<br>"

    return result


# ==========================
# DEBUG
# ==========================

@app.route('/debug')
def debug():

    conn = get_db()

    students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    attendance = conn.execute(
        "SELECT COUNT(*) FROM attendance"
    ).fetchone()[0]

    return f"""
    Students = {students}
    <br><br>
    Attendance = {attendance}
    """


# ==========================
# LOGOUT
# ==========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# ==========================
# RUN APP
# ==========================

if __name__ == '__main__':
    app.run(debug=True)
