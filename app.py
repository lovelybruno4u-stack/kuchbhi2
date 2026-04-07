import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv
from db import db
from ai import ai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_fallback_key")

# ---- AUTHENTICATION DECORATORS & HELPERS ----

from functools import wraps

def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Unauthorized"}), 401
                return redirect(url_for('login'))
            if role and session.get('user_role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({"error": "Forbidden"}), 403
                return "Unauthorized access", 403
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# ---- ROUTES: AUTHENTICATION ----

@app.route('/')
def index():
    if 'user_role' in session:
        if session['user_role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        # Simple authentication logic for demonstration
        if role == 'teacher' and username == 'admin' and password == 'admin':
            session['user_role'] = 'teacher'
            session['user_id'] = 'teacher_1'
            session['name'] = 'Teacher'
            return redirect(url_for('teacher_dashboard'))
        elif role == 'student':
            students = db.get_sheet_records('students')
            for student in students:
                # For basic security in this mock implementation, we expect password to match the roll number or email
                # In a production app, this should be a proper hashed password lookup
                if (student.get('email') == username or str(student.get('roll')) == username) and (password == str(student.get('roll')) or password == student.get('email')):
                    session['user_role'] = 'student'
                    session['user_id'] = str(student.get('id'))
                    session['name'] = student.get('name')
                    return redirect(url_for('student_dashboard'))
            flash("Invalid student credentials", "error")
        else:
            flash("Invalid credentials", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---- ROUTES: TEACHER PAGES ----

@app.route('/teacher')
@login_required(role='teacher')
def teacher_dashboard():
    students = db.get_sheet_records('students')
    attendance = db.get_sheet_records('attendance')

    total_students = len(students)
    today = datetime.now().strftime('%Y-%m-%d')
    today_attendance = [a for a in attendance if a.get('date') == today and a.get('status') == 'present']

    return render_template('dashboard.html',
                           total_students=total_students,
                           today_present=len(today_attendance))

@app.route('/teacher/students')
@login_required(role='teacher')
def teacher_students():
    students = db.get_sheet_records('students')
    return render_template('students.html', students=students)

@app.route('/teacher/attendance')
@login_required(role='teacher')
def teacher_attendance():
    students = db.get_sheet_records('students')
    return render_template('attendance.html', students=students)

@app.route('/teacher/videos')
@login_required(role='teacher')
def teacher_videos():
    videos = db.get_sheet_records('videos')
    subjects = db.get_sheet_records('subjects')
    return render_template('videos.html', videos=videos, subjects=subjects)

@app.route('/teacher/subjects')
@login_required(role='teacher')
def teacher_subjects():
    subjects = db.get_sheet_records('subjects')
    return render_template('subjects.html', subjects=subjects)

@app.route('/teacher/announcements')
@login_required(role='teacher')
def teacher_announcements():
    announcements = db.get_sheet_records('announcements')
    return render_template('announcements.html', announcements=announcements)

@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def teacher_ai_tools():
    return render_template('ai_tools.html')

# ---- ROUTES: STUDENT PAGES ----

@app.route('/student')
@login_required(role='student')
def student_dashboard():
    announcements = db.get_sheet_records('announcements')
    recent_announcements = announcements[-3:] if announcements else []
    return render_template('student_dashboard.html',
                           name=session.get('name'),
                           announcements=recent_announcements)

@app.route('/student/videos')
@login_required(role='student')
def student_videos():
    videos = db.get_sheet_records('videos')
    return render_template('my_videos.html', videos=videos)

@app.route('/student/attendance')
@login_required(role='student')
def student_attendance():
    all_attendance = db.get_sheet_records('attendance')
    my_id = session.get('user_id')
    my_attendance = [a for a in all_attendance if str(a.get('student_id')) == my_id]
    return render_template('attendance_view.html', attendance=my_attendance)

@app.route('/student/chatbot')
@login_required(role='student')
def student_chatbot():
    return render_template('chatbot.html')

@app.route('/student/announcements')
@login_required(role='student')
def student_announcements():
    announcements = db.get_sheet_records('announcements')
    return render_template('announcements_view.html', announcements=announcements)

# ---- API ENDPOINTS: CRUD & AI ----

@app.route('/api/students', methods=['POST'])
@login_required(role='teacher')
def api_add_student():
    data = request.json
    new_id = str(uuid.uuid4())[:8]
    row = [new_id, data.get('name'), data.get('class'), data.get('roll'),
           data.get('phone'), data.get('email'), data.get('parent')]
    success = db.append_row('students', row)
    return jsonify({"success": success})

@app.route('/api/students/<student_id>', methods=['PUT'])
@login_required(role='teacher')
def api_update_student(student_id):
    data = request.json
    new_values = {
        'name': data.get('name'),
        'class': data.get('class'),
        'roll': data.get('roll'),
        'phone': data.get('phone'),
        'email': data.get('email'),
        'parent': data.get('parent')
    }
    success = db.update_row('students', 'id', student_id, new_values)
    return jsonify({"success": success})

@app.route('/api/students/<student_id>', methods=['DELETE'])
@login_required(role='teacher')
def api_delete_student(student_id):
    success = db.delete_row('students', 'id', student_id)
    return jsonify({"success": success})

@app.route('/api/attendance', methods=['POST'])
@login_required(role='teacher')
def api_mark_attendance():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    records = data.get('records', []) # list of {student_id: id, status: status}

    success = True
    for rec in records:
        row = [date, rec.get('student_id'), rec.get('status')]
        if not db.append_row('attendance', row):
            success = False

    return jsonify({"success": success})

@app.route('/api/videos', methods=['POST'])
@login_required(role='teacher')
def api_add_video():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    row = [date, data.get('subject'), data.get('drive_link')]
    success = db.append_row('videos', row)
    return jsonify({"success": success})

@app.route('/api/subjects', methods=['POST'])
@login_required(role='teacher')
def api_add_subject():
    data = request.json
    row = [data.get('subject_name')]
    success = db.append_row('subjects', row)
    return jsonify({"success": success})

@app.route('/api/subjects/<subject_name>', methods=['PUT'])
@login_required(role='teacher')
def api_update_subject(subject_name):
    data = request.json
    new_values = {
        'subject_name': data.get('subject_name')
    }
    success = db.update_row('subjects', 'subject_name', subject_name, new_values)
    return jsonify({"success": success})

@app.route('/api/subjects/<subject_name>', methods=['DELETE'])
@login_required(role='teacher')
def api_delete_subject(subject_name):
    success = db.delete_row('subjects', 'subject_name', subject_name)
    return jsonify({"success": success})

@app.route('/api/announcements', methods=['POST'])
@login_required(role='teacher')
def api_add_announcement():
    data = request.json
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    row = [date, data.get('message')]
    success = db.append_row('announcements', row)
    return jsonify({"success": success})

# AI Endpoints

@app.route('/api/ai/doubt', methods=['POST'])
@login_required(role='student')
def api_ai_doubt():
    question = request.json.get('question')
    answer = ai.solve_doubt(question)
    return jsonify({"answer": answer})

@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def api_ai_chat():
    message = request.json.get('message')
    reply = ai.study_chatbot(message)
    return jsonify({"reply": reply})

@app.route('/api/ai/attendance_insight', methods=['POST'])
@login_required(role='teacher')
def api_ai_attendance():
    # Fetch recent attendance to send to AI
    attendance_records = db.get_sheet_records('attendance')[-50:] # last 50 records
    attendance_str = str(attendance_records)
    insight = ai.analyze_attendance(attendance_str)
    return jsonify({"insight": insight})

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required(role='teacher')
def api_ai_video_summary():
    topic = request.json.get('topic')
    summary = ai.summarize_video(topic)
    return jsonify({"summary": summary})

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def api_ai_quiz():
    subject = request.json.get('subject')
    topic = request.json.get('topic')
    quiz = ai.generate_quiz(subject, topic)
    return jsonify({"quiz": quiz})

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='teacher')
def api_ai_announcement():
    prompt = request.json.get('prompt')
    announcement = ai.generate_announcement(prompt)
    return jsonify({"announcement": announcement})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
