from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_default_key")

from datetime import datetime
# Import db
from db import db
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    if 'role' in session:
        if session['role'] == 'teacher':
            return redirect('/teacher/dashboard')
        elif session['role'] == 'student':
            return redirect('/student/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        password = request.form.get('password') # Simplistic auth for now
        student_id = request.form.get('student_id')

        if role == 'teacher':
            # Hardcoded admin password for simplicity as per requirements (secure login session system)
            if password == 'admin123':
                session['role'] = 'teacher'
                session['user_id'] = 'admin'
                return redirect('/teacher/dashboard')
            else:
                flash("Invalid teacher credentials.", "error")
        elif role == 'student':
            student = db.get_student_by_id(student_id)
            if student:
                session['role'] = 'student'
                session['user_id'] = student_id
                session['user_name'] = student.get('name', 'Student')
                return redirect('/student/dashboard')
            else:
                flash("Student ID not found.", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- Middleware-like Decorators ---
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'teacher':
            flash("Access denied. Teacher role required.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'student':
            flash("Access denied. Student role required.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Teacher Routes ---

@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    students = db.get_all_students()
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = db.get_attendance_by_date(today)
    present_count = sum(1 for a in today_attendance if a.get('status') == 'Present')

    return render_template('teacher/dashboard.html',
                           total_students=len(students),
                           today_attendance=f"{present_count}/{len(students)}")

@app.route('/teacher/students', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_students():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            data = {
                'name': request.form.get('name'),
                'class': request.form.get('class'),
                'roll': request.form.get('roll'),
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'parent': request.form.get('parent')
            }
            db.add_student(data)
            flash("Student added successfully.")
        elif action == 'delete':
            student_id = request.form.get('student_id')
            db.delete_student(student_id)
            flash("Student deleted successfully.")
        return redirect(url_for('teacher_students'))

    students = db.get_all_students()
    return render_template('teacher/students.html', students=students)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_attendance():
    if request.method == 'POST':
        date = request.form.get('date') or datetime.now().strftime("%Y-%m-%d")
        student_id = request.form.get('student_id')
        status = request.form.get('status') # 'Present' or 'Absent'
        db.mark_attendance(date, student_id, status)
        return jsonify({"success": True})

    students = db.get_all_students()
    date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    attendance_records = db.get_attendance_by_date(date)

    # Map attendance by student_id
    att_map = {str(a['student_id']): a['status'] for a in attendance_records}

    return render_template('teacher/attendance.html', students=students, date=date, att_map=att_map)

@app.route('/teacher/videos', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_videos():
    if request.method == 'POST':
        date = request.form.get('date')
        subject = request.form.get('subject')
        drive_link = request.form.get('drive_link')
        db.add_video(date, subject, drive_link)
        flash("Video added successfully.")
        return redirect(url_for('teacher_videos'))

    videos = db.get_all_videos()
    subjects = db.get_all_subjects()
    return render_template('teacher/videos.html', videos=videos, subjects=subjects)

@app.route('/teacher/subjects', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_subjects():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            subject_name = request.form.get('subject_name')
            db.add_subject(subject_name)
        elif action == 'delete':
            subject_name = request.form.get('subject_name')
            db.delete_subject(subject_name)
        return redirect(url_for('teacher_subjects'))

    subjects = db.get_all_subjects()
    return render_template('teacher/subjects.html', subjects=subjects)

@app.route('/teacher/announcements', methods=['GET', 'POST'])
@login_required
@teacher_required
def teacher_announcements():
    if request.method == 'POST':
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = request.form.get('message')
        db.add_announcement(date, message)
        flash("Announcement added.")
        return redirect(url_for('teacher_announcements'))

    announcements = db.get_all_announcements()
    return render_template('teacher/announcements.html', announcements=announcements)

@app.route('/teacher/ai_tools')
@login_required
@teacher_required
def teacher_ai_tools():
    return render_template('teacher/ai_tools.html')

# --- AI API Routes (Teacher) ---

@app.route('/api/ai/announcement', methods=['POST'])
@login_required
@teacher_required
def api_ai_announcement():
    data = request.json
    topic = data.get('topic', '')
    prompt = f"Write a professional coaching class announcement about: {topic}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/attendance_insight', methods=['POST'])
@login_required
@teacher_required
def api_ai_attendance_insight():
    attendance_data = db.get_all_attendance()
    # Serialize data simply for prompt
    data_str = str(attendance_data)
    prompt = f"Analyze attendance data and provide insights: {data_str[:2000]}" # Limit length
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required
@teacher_required
def api_ai_video_summary():
    data = request.json
    topic = data.get('topic', '')
    prompt = f"Generate summary notes for revision for the topic: {topic}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/quiz_generator', methods=['POST'])
@login_required
@teacher_required
def api_ai_quiz_generator():
    data = request.json
    topic = data.get('topic', '')
    prompt = f"Generate 5 MCQ questions with answers for the topic: {topic}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Student Routes ---

@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    # Show summary
    user_name = session.get('user_name')
    return render_template('student/student_dashboard.html', user_name=user_name)

@app.route('/student/my_videos')
@login_required
@student_required
def student_my_videos():
    videos = db.get_all_videos()
    return render_template('student/my_videos.html', videos=videos)

@app.route('/student/attendance')
@login_required
@student_required
def student_attendance():
    student_id = session.get('user_id')
    attendance = db.get_attendance_for_student(student_id)
    return render_template('student/attendance_view.html', attendance=attendance)

@app.route('/student/chatbot')
@login_required
@student_required
def student_chatbot():
    return render_template('student/chatbot.html')

@app.route('/student/announcements')
@login_required
@student_required
def student_announcements():
    announcements = db.get_all_announcements()
    return render_template('student/announcements_view.html', announcements=announcements)

# --- AI API Routes (Student) ---

@app.route('/api/ai/doubt_solver', methods=['POST'])
@login_required
@student_required
def api_ai_doubt_solver():
    data = request.json
    question = data.get('question', '')
    prompt = f"Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution. Question: {question}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/chatbot', methods=['POST'])
@login_required
@student_required
def api_ai_chatbot():
    data = request.json
    message = data.get('message', '')
    prompt = f"You are a friendly and helpful study tutor for school students. Answer the following: {message}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
