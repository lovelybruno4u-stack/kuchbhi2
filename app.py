import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super_secret_dev_key_12345')

# ------------------------------------------------------------------------------
# MOCK DATABASE SETUP (Fallback if Google Sheets fails)
# ------------------------------------------------------------------------------
class MockDB:
    def __init__(self):
        self.students = []
        self.attendance = []
        self.videos = []
        self.subjects = []
        self.announcements = []
        self.student_id_counter = 1

MOCK_DB = MockDB()
USE_MOCK = False

# ------------------------------------------------------------------------------
# GOOGLE SHEETS SETUP
# ------------------------------------------------------------------------------
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_file = 'CREDENTIALS.JSON'

    if os.path.exists(creds_file) and os.path.getsize(creds_file) > 10:
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
    elif os.environ.get('GOOGLE_CREDENTIALS'):
        creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        raise Exception("No credentials found")

    client = gspread.authorize(credentials)

    # Try to open the sheet, assuming it's named 'Aswathama Classes' or similar.
    # For robust deployment, users should set SHEET_NAME env var.
    sheet_name = os.environ.get('SHEET_NAME', 'Aswathama Classes')
    try:
        sh = client.open(sheet_name)
    except:
        # If specific name fails, just open the first spreadsheet available to the service account
        sh = client.openall()[0]

    students_sheet = sh.worksheet('students')
    attendance_sheet = sh.worksheet('attendance')
    videos_sheet = sh.worksheet('videos')
    subjects_sheet = sh.worksheet('subjects')
    announcements_sheet = sh.worksheet('announcements')
    print("Successfully connected to Google Sheets")
except Exception as e:
    print(f"Failed to connect to Google Sheets: {e}. Falling back to in-memory MOCK DB.")
    USE_MOCK = True

# ------------------------------------------------------------------------------
# DB HELPER FUNCTIONS
# ------------------------------------------------------------------------------
def get_all_records(sheet_name):
    if USE_MOCK:
        return getattr(MOCK_DB, sheet_name)

    sheet = globals()[f"{sheet_name}_sheet"]
    return sheet.get_all_records()

def append_row(sheet_name, row_data):
    if USE_MOCK:
        if sheet_name == 'students':
            # expects id, name, class, roll, phone, email, parent
            data = dict(zip(['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'], row_data))
            MOCK_DB.students.append(data)
        elif sheet_name == 'attendance':
            data = dict(zip(['date', 'student_id', 'status'], row_data))
            MOCK_DB.attendance.append(data)
        elif sheet_name == 'videos':
            data = dict(zip(['date', 'subject', 'drive_link'], row_data))
            MOCK_DB.videos.append(data)
        elif sheet_name == 'subjects':
            data = dict(zip(['subject_name'], row_data))
            MOCK_DB.subjects.append(data)
        elif sheet_name == 'announcements':
            data = dict(zip(['date', 'message'], row_data))
            MOCK_DB.announcements.append(data)
        return

    sheet = globals()[f"{sheet_name}_sheet"]
    sheet.append_row(row_data)

def generate_student_id():
    if USE_MOCK:
        vid = MOCK_DB.student_id_counter
        MOCK_DB.student_id_counter += 1
        return str(vid)

    students = get_all_records('students')
    if not students:
        return "1"
    max_id = 0
    for s in students:
        try:
            if int(s['id']) > max_id:
                max_id = int(s['id'])
        except:
            pass
    return str(max_id + 1)

# ------------------------------------------------------------------------------
# OPENAI SETUP
# ------------------------------------------------------------------------------
openai_client = None
if os.environ.get('OPENAI_API_KEY'):
    openai_client = OpenAI()

# ------------------------------------------------------------------------------
# AUTH DECORATORS
# ------------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'teacher':
            if request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden"}), 403
            flash("Access denied: Teachers only")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'student':
            if request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden"}), 403
            flash("Access denied: Students only")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------------------------------------------------------
# AUTH ROUTES
# ------------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    if 'role' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        if role == 'teacher':
            if username == 'admin' and password == 'admin':
                session['role'] = 'teacher'
                session['name'] = 'Admin Teacher'
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid teacher credentials")

        elif role == 'student':
            students = get_all_records('students')

            # Special demo fallback for students
            if username == 'student' and password == 'student':
                session['role'] = 'student'
                if students:
                    # Assign the first available student to prevent DB mismatches
                    student = students[0]
                    session['user_id'] = str(student.get('id', ''))
                    session['name'] = str(student.get('name', 'Demo Student'))
                    session['student_class'] = str(student.get('class', ''))
                    session['student_roll'] = str(student.get('roll', ''))
                else:
                    session['user_id'] = 'demo_id'
                    session['name'] = 'Demo Student'
                    session['student_class'] = '10'
                    session['student_roll'] = '1'
                return redirect(url_for('student_dashboard'))

            # Actual student verification
            for s in students:
                if str(s.get('roll')) == username and str(s.get('phone')) == password:
                    session['role'] = 'student'
                    session['user_id'] = str(s.get('id', ''))
                    session['name'] = str(s.get('name', ''))
                    session['student_class'] = str(s.get('class', ''))
                    session['student_roll'] = str(s.get('roll', ''))
                    return redirect(url_for('student_dashboard'))

            flash("Invalid student credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------------------------------------------------------------------
# TEACHER ROUTES
# ------------------------------------------------------------------------------
@app.route('/dashboard')
@teacher_required
def dashboard():
    students = get_all_records('students')
    total_students = len(students)
    return render_template('dashboard.html', total_students=total_students)

@app.route('/students', methods=['GET'])
@teacher_required
def students():
    student_list = get_all_records('students')
    search_q = request.args.get('q', '').lower()
    if search_q:
        student_list = [s for s in student_list if search_q in str(s.get('name', '')).lower() or search_q in str(s.get('roll', '')) or search_q in str(s.get('class', ''))]
    return render_template('students.html', students=student_list, search_q=search_q)

@app.route('/students/add', methods=['POST'])
@teacher_required
def add_student():
    name = request.form.get('name')
    class_name = request.form.get('class_name')
    roll = request.form.get('roll')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    parent = request.form.get('parent', '')

    new_id = generate_student_id()
    append_row('students', [new_id, name, class_name, roll, phone, email, parent])

    flash("Student added successfully!")
    return redirect(url_for('students'))


@app.route('/students/delete/<student_id>', methods=['POST'])
@teacher_required
def delete_student(student_id):
    if USE_MOCK:
        MOCK_DB.students = [s for s in MOCK_DB.students if str(s['id']) != student_id]
    else:
        # In a real app we'd find the row and delete it, for simplicity with gspread we can just fetch, modify, update
        records = students_sheet.get_all_records()
        row = next((i + 2 for i, r in enumerate(records) if str(r['id']) == student_id), None)
        if row:
            students_sheet.delete_rows(row)
    flash("Student deleted successfully")
    return redirect(url_for('students'))

@app.route('/students/edit/<student_id>', methods=['POST'])
@teacher_required
def edit_student(student_id):
    name = request.form.get('name')
    class_name = request.form.get('class_name')
    roll = request.form.get('roll')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    parent = request.form.get('parent', '')

    if USE_MOCK:
        for s in MOCK_DB.students:
            if str(s['id']) == student_id:
                s.update({'name': name, 'class': class_name, 'roll': roll, 'phone': phone, 'email': email, 'parent': parent})
    else:
        records = students_sheet.get_all_records()
        row = next((i + 2 for i, r in enumerate(records) if str(r['id']) == student_id), None)
        if row:
            students_sheet.update(f'A{row}:G{row}', [[student_id, name, class_name, roll, phone, email, parent]])
    flash("Student updated successfully")
    return redirect(url_for('students'))

@app.route('/subjects/delete/<subject_name>', methods=['POST'])
@teacher_required
def delete_subject(subject_name):
    if USE_MOCK:
        MOCK_DB.subjects = [s for s in MOCK_DB.subjects if s['subject_name'] != subject_name]
    else:
        records = subjects_sheet.get_all_records()
        row = next((i + 2 for i, r in enumerate(records) if r['subject_name'] == subject_name), None)
        if row:
            subjects_sheet.delete_rows(row)
    flash("Subject deleted successfully")
    return redirect(url_for('subjects'))

@app.route('/attendance', methods=['GET'])
@teacher_required
def attendance():
    student_list = get_all_records('students')
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('attendance.html', students=student_list, today=today)

@app.route('/attendance/save', methods=['POST'])
@teacher_required
def save_attendance():
    date = request.form.get('date')
    student_list = get_all_records('students')

    for s in student_list:
        status = request.form.get(f"status_{s['id']}")
        if status:
            append_row('attendance', [date, str(s['id']), status])

    flash("Attendance saved successfully!")
    return redirect(url_for('attendance'))

@app.route('/videos', methods=['GET'])
@teacher_required
def videos():
    video_list = get_all_records('videos')
    subject_list = get_all_records('subjects')
    today = datetime.now().strftime('%Y-%m-%d')
    # reverse sort videos so newest is first
    video_list = sorted(video_list, key=lambda x: x.get('date', ''), reverse=True)
    return render_template('videos.html', videos=video_list, subjects=subject_list, today=today)

@app.route('/videos/add', methods=['POST'])
@teacher_required
def add_video():
    date = request.form.get('date')
    subject = request.form.get('subject')
    drive_link = request.form.get('drive_link')

    append_row('videos', [date, subject, drive_link])
    flash("Video added successfully!")
    return redirect(url_for('videos'))

@app.route('/subjects', methods=['GET'])
@teacher_required
def subjects():
    subject_list = get_all_records('subjects')
    return render_template('subjects.html', subjects=subject_list)

@app.route('/subjects/add', methods=['POST'])
@teacher_required
def add_subject():
    name = request.form.get('subject_name')
    if name:
        append_row('subjects', [name])
        flash("Subject added successfully!")
    return redirect(url_for('subjects'))

@app.route('/announcements', methods=['GET'])
@teacher_required
def announcements():
    ann_list = get_all_records('announcements')
    # reverse sort
    ann_list = sorted(ann_list, key=lambda x: x.get('date', ''), reverse=True)
    return render_template('announcements.html', announcements=ann_list)

@app.route('/announcements/add', methods=['POST'])
@teacher_required
def add_announcement():
    message = request.form.get('message')
    if message:
        date = datetime.now().strftime('%Y-%m-%d %H:%M')
        append_row('announcements', [date, message])
        flash("Announcement posted successfully!")
    return redirect(url_for('announcements'))

@app.route('/ai_tools')
@teacher_required
def ai_tools():
    return render_template('ai_tools.html')

# ------------------------------------------------------------------------------
# STUDENT ROUTES
# ------------------------------------------------------------------------------
@app.route('/student/dashboard')
@student_required
def student_dashboard():
    return render_template('student_dashboard.html',
                           student_class=session.get('student_class'),
                           student_roll=session.get('student_roll'))

@app.route('/student/my_videos')
@student_required
def my_videos():
    all_videos = get_all_records('videos')
    # reverse sort
    all_videos = sorted(all_videos, key=lambda x: x.get('date', ''), reverse=True)
    return render_template('my_videos.html', videos=all_videos)

@app.route('/student/attendance')
@student_required
def attendance_view():
    all_att = get_all_records('attendance')
    user_id = str(session.get('user_id'))
    my_att = [a for a in all_att if str(a.get('student_id')) == user_id]
    # reverse sort
    my_att = sorted(my_att, key=lambda x: x.get('date', ''), reverse=True)
    return render_template('attendance_view.html', attendance=my_att)

@app.route('/student/announcements')
@student_required
def announcements_view():
    ann_list = get_all_records('announcements')
    # reverse sort
    ann_list = sorted(ann_list, key=lambda x: x.get('date', ''), reverse=True)
    return render_template('announcements_view.html', announcements=ann_list)

@app.route('/student/chatbot')
@student_required
def chatbot():
    return render_template('chatbot.html')

# ------------------------------------------------------------------------------
# AI API ROUTES
# ------------------------------------------------------------------------------
@app.route('/api/ai/announcement', methods=['POST'])
@login_required
def api_ai_announcement():
    if not openai_client:
        return jsonify({"error": "OpenAI API key not configured"}), 500

    data = request.json
    topic = data.get('topic', '')

    prompt = f"Write a professional coaching class announcement about: {topic}. Keep it concise and professional."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        msg = response.choices[0].message.content
        return jsonify({"announcement": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/attendance', methods=['POST'])
@login_required
def api_ai_attendance():
    if not openai_client:
        return jsonify({"error": "OpenAI API key not configured"}), 500

    try:
        att = get_all_records('attendance')
        students = get_all_records('students')

        # Build student name map
        student_map = {str(s.get('id')): s.get('name', 'Unknown') for s in students}

        # Build raw stats
        stats = {}
        for a in att:
            sid = str(a.get('student_id'))
            if sid not in stats:
                stats[sid] = {'present': 0, 'absent': 0, 'name': student_map.get(sid, f"ID:{sid}")}

            if a.get('status', '').lower() == 'present':
                stats[sid]['present'] += 1
            else:
                stats[sid]['absent'] += 1

        if not stats:
            return jsonify({"result": "No attendance data available to analyze."})

        # Send raw structured data to AI
        prompt = "Analyze attendance data and provide insights. Here is the raw data mapping student names to present/absent counts:\n\n"
        prompt += json.dumps(stats, indent=2)
        prompt += "\n\nIdentify irregular students, calculate overall attendance percentages, and suggest actions in a short summary."

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        msg = response.choices[0].message.content
        return jsonify({"result": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required
def api_ai_video_summary():
    if not openai_client:
        return jsonify({"error": "OpenAI API key not configured"}), 500

    data = request.json
    topic = data.get('topic', '')

    prompt = f"Generate summary notes for revision on the topic: {topic}. Include key points."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        msg = response.choices[0].message.content
        return jsonify({"result": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
@login_required
def api_ai_quiz():
    if not openai_client:
        return jsonify({"error": "OpenAI API key not configured"}), 500

    data = request.json
    topic = data.get('topic', '')

    prompt = f"Generate 5 MCQ questions with answers on the topic: {topic}."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        msg = response.choices[0].message.content
        return jsonify({"result": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def api_ai_chat():
    if not openai_client:
        return jsonify({"error": "OpenAI API key not configured"}), 500

    data = request.json
    chat_history = data.get('chat_history', [])

    # Prepend system prompt
    system_msg = {
        "role": "system",
        "content": "You are an AI Doubt Solver and friendly AI Study Chatbot for a school student. Explain this concept in very simple words for a school student. If it is a math question, give a step by step solution. Provide study tips and act as a friendly tutor."
    }

    messages = [system_msg] + chat_history

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        msg = response.choices[0].message.content
        return jsonify({"reply": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # When deployed on render or run with gunicorn, this block is bypassed.
    # Run locally with python app.py
    app.run(debug=True, host='127.0.0.1', port=5000)
