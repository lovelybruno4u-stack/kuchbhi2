import os
import json
import uuid
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_session_key')

openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'CREDENTIALS.JSON'
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

fallback_db = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

use_mock_db = False

def get_sheet(sheet_name):
    global use_mock_db
    if use_mock_db:
        return None
    try:
        if os.path.exists(CREDENTIALS_FILE) and SHEET_ID:
            with open(CREDENTIALS_FILE, 'r') as f:
                creds_data = json.load(f)
                if 'placeholder' in creds_data:
                    use_mock_db = True
                    return None
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            gc = gspread.authorize(creds)
            spreadsheet = gc.open_by_key(SHEET_ID)
            return spreadsheet.worksheet(sheet_name)
        else:
            use_mock_db = True
            return None
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        use_mock_db = True
        return None

def get_all_records(sheet_name):
    if use_mock_db:
        return fallback_db.get(sheet_name, [])
    try:
        sheet = get_sheet(sheet_name)
        if sheet:
            return sheet.get_all_records()
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
    return fallback_db.get(sheet_name, [])

def append_row(sheet_name, row_data):
    if use_mock_db:
        schemas = {
            'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'],
            'attendance': ['date', 'student_id', 'status'],
            'videos': ['date', 'subject', 'drive_link'],
            'subjects': ['subject_name'],
            'announcements': ['date', 'message']
        }
        schema = schemas.get(sheet_name, [])
        record = {schema[i]: row_data[i] for i in range(len(row_data))}
        fallback_db[sheet_name].append(record)
        return True
    try:
        sheet = get_sheet(sheet_name)
        if sheet:
            sheet.append_row(row_data)
            return True
    except Exception as e:
        print(f"Error appending to {sheet_name}: {e}")
    return False

def update_student(student_id, update_data):
    if use_mock_db:
        for s in fallback_db['students']:
            if str(s['id']) == str(student_id):
                s.update(update_data)
                return True
        return False
    try:
        sheet = get_sheet('students')
        records = sheet.get_all_records()
        row_index = 2
        for r in records:
            if str(r['id']) == str(student_id):
                # Update cells
                cells = sheet.range(f'B{row_index}:G{row_index}')
                cells[0].value = update_data.get('name', r['name'])
                cells[1].value = update_data.get('class', r['class'])
                cells[2].value = update_data.get('roll', r['roll'])
                cells[3].value = update_data.get('phone', r['phone'])
                cells[4].value = update_data.get('email', r['email'])
                cells[5].value = update_data.get('parent', r['parent'])
                sheet.update_cells(cells)
                return True
            row_index += 1
    except Exception as e:
        print(f"Error updating student: {e}")
    return False

def delete_student(student_id):
    if use_mock_db:
        fallback_db['students'] = [s for s in fallback_db['students'] if str(s['id']) != str(student_id)]
        return True
    try:
        sheet = get_sheet('students')
        records = sheet.get_all_records()
        row_index = 2
        for r in records:
            if str(r['id']) == str(student_id):
                sheet.delete_rows(row_index)
                return True
            row_index += 1
    except Exception as e:
        print(f"Error deleting student: {e}")
    return False

def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized'}), 401
                return redirect(url_for('login_page'))
            if role and session.get('role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Forbidden'}), 403
                return redirect(url_for('login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/')
def index():
    if 'user' in session:
        if session.get('role') == 'Teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.json
    role = data.get('role')
    username = data.get('username')
    password = data.get('password')

    if role == 'Teacher':
        if username == 'admin' and password == 'admin':
            session['user'] = 'admin'
            session['role'] = 'Teacher'
            return jsonify({'success': True, 'redirect': url_for('teacher_dashboard')})
        return jsonify({'success': False, 'error': 'Invalid teacher credentials'})

    elif role == 'Student':
        students = get_all_records('students')
        for s in students:
            # Login with email/phone as username, roll number as password
            if (str(s['email']) == username or str(s['phone']) == username) and str(s['roll']) == password:
                session['user'] = s['id']
                session['name'] = s['name']
                session['role'] = 'Student'
                return jsonify({'success': True, 'redirect': url_for('student_dashboard')})
        return jsonify({'success': False, 'error': 'Invalid student credentials'})

    return jsonify({'success': False, 'error': 'Invalid role'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- TEACHER ROUTES ---
@app.route('/teacher/dashboard')
@login_required(role='Teacher')
def teacher_dashboard():
    return render_template('dashboard.html')

@app.route('/teacher/students')
@login_required(role='Teacher')
def teacher_students():
    return render_template('students.html')

@app.route('/teacher/attendance')
@login_required(role='Teacher')
def teacher_attendance():
    return render_template('attendance.html')

@app.route('/teacher/videos')
@login_required(role='Teacher')
def teacher_videos():
    return render_template('videos.html')

@app.route('/teacher/subjects')
@login_required(role='Teacher')
def teacher_subjects():
    return render_template('subjects.html')

@app.route('/teacher/announcements')
@login_required(role='Teacher')
def teacher_announcements():
    return render_template('announcements.html')

@app.route('/teacher/ai-tools')
@login_required(role='Teacher')
def teacher_ai_tools():
    return render_template('ai_tools.html')

# --- STUDENT ROUTES ---
@app.route('/student/dashboard')
@login_required(role='Student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/student/my-videos')
@login_required(role='Student')
def my_videos():
    return render_template('my_videos.html')

@app.route('/student/attendance')
@login_required(role='Student')
def attendance_view():
    return render_template('attendance_view.html')

@app.route('/student/chatbot')
@login_required(role='Student')
def chatbot():
    return render_template('chatbot.html')

@app.route('/student/announcements')
@login_required(role='Student')
def student_announcements_view():
    return render_template('announcements_view.html')

# --- API ENDPOINTS ---

# STUDENTS
@app.route('/api/students', methods=['GET'])
@login_required(role='Teacher')
def api_get_students():
    students = get_all_records('students')
    return jsonify({'success': True, 'data': students})

@app.route('/api/students', methods=['POST'])
@login_required(role='Teacher')
def api_add_student():
    data = request.json
    new_id = str(uuid.uuid4())[:8]
    row = [new_id, data.get('name'), data.get('class'), data.get('roll'), data.get('phone'), data.get('email'), data.get('parent')]
    if append_row('students', row):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Database error'})

@app.route('/api/students/<student_id>', methods=['PUT', 'DELETE'])
@login_required(role='Teacher')
def api_manage_student(student_id):
    if request.method == 'PUT':
        data = request.json
        if update_student(student_id, data):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Failed to update'})
    elif request.method == 'DELETE':
        if delete_student(student_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Failed to delete'})

# ATTENDANCE
@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def api_attendance():
    if request.method == 'GET':
        records = get_all_records('attendance')
        if session.get('role') == 'Student':
            records = [r for r in records if str(r.get('student_id')) == str(session.get('user'))]
        return jsonify({'success': True, 'data': records})

    if request.method == 'POST' and session.get('role') == 'Teacher':
        data = request.json
        date = data.get('date')
        attendance_data = data.get('attendance') # list of dicts: {'student_id': '...', 'status': 'Present'/'Absent'}

        # In a real app we'd update existing records or insert new ones.
        # For simplicity, we just append rows. If using mock db, this will be quick.
        for item in attendance_data:
            append_row('attendance', [date, item['student_id'], item['status']])
        return jsonify({'success': True})

# VIDEOS
@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'GET':
        records = get_all_records('videos')
        return jsonify({'success': True, 'data': records})
    if request.method == 'POST' and session.get('role') == 'Teacher':
        data = request.json
        append_row('videos', [data.get('date'), data.get('subject'), data.get('drive_link')])
        return jsonify({'success': True})

# SUBJECTS
@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required()
def api_subjects():
    if request.method == 'GET':
        records = get_all_records('subjects')
        return jsonify({'success': True, 'data': records})
    if request.method == 'POST' and session.get('role') == 'Teacher':
        data = request.json
        append_row('subjects', [data.get('subject_name')])
        return jsonify({'success': True})

# ANNOUNCEMENTS
@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'GET':
        records = get_all_records('announcements')
        return jsonify({'success': True, 'data': records})
    if request.method == 'POST' and session.get('role') == 'Teacher':
        data = request.json
        append_row('announcements', [datetime.now().strftime("%Y-%m-%d"), data.get('message')])
        return jsonify({'success': True})

# --- AI ENDPOINTS ---

@app.route('/api/ai/doubt-solver', methods=['POST'])
@login_required(role='Student')
def api_doubt_solver():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})
    data = request.json
    question = data.get('question', '')
    prompt = "Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({'success': True, 'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/chatbot', methods=['POST'])
@login_required(role='Student')
def api_chatbot():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})
    data = request.json
    messages = data.get('messages', [])
    prompt = "You are a friendly and helpful study tutor for a school student. Answer their concept doubts, give exam prep advice, and study tips in a student-friendly tone."

    api_messages = [{"role": "system", "content": prompt}] + messages

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )
        return jsonify({'success': True, 'reply': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/attendance-insight', methods=['POST'])
@login_required(role='Teacher')
def api_attendance_insight():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})

    # Needs raw attendance data
    attendance = get_all_records('attendance')
    students = get_all_records('students')
    student_map = {str(s['id']): s['name'] for s in students}

    # Build dictionary of student IDs mapped to present/absent counts
    data_for_ai = {}
    for r in attendance:
        sid = str(r['student_id'])
        sname = student_map.get(sid, sid)
        status = r['status'].lower()
        if sname not in data_for_ai:
            data_for_ai[sname] = {'present': 0, 'absent': 0}
        if status == 'present':
            data_for_ai[sname]['present'] += 1
        elif status == 'absent':
            data_for_ai[sname]['absent'] += 1

    prompt = "Analyze attendance data and provide insights. Identify which students are irregular, calculate their attendance percentage, and suggest actions."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(data_for_ai)}
            ]
        )
        return jsonify({'success': True, 'insight': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/video-summary', methods=['POST'])
@login_required(role='Teacher')
def api_video_summary():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})
    data = request.json
    topic = data.get('topic', '')
    prompt = "Generate summary notes for revision based on the following topic. Include a summary, key points, and revision notes."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'success': True, 'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/quiz-generator', methods=['POST'])
@login_required(role='Teacher')
def api_quiz_generator():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})
    data = request.json
    topic = data.get('topic', '')
    prompt = "Generate 5 MCQ questions with answers. Format them clearly with Question, Options (A, B, C, D), and Answer."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'success': True, 'quiz': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='Teacher')
def api_ai_announcement():
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key missing'})
    data = request.json
    topic = data.get('topic', '')
    prompt = "Write a professional coaching class announcement. Make it clear and concise."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'success': True, 'announcement': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/teacher/dashboard-stats', methods=['GET'])
@login_required(role='Teacher')
def api_dashboard_stats():
    students = get_all_records('students')
    attendance = get_all_records('attendance')
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = [a for a in attendance if str(a.get('date')) == today]
    present_count = len([a for a in today_attendance if a.get('status', '').lower() == 'present'])

    return jsonify({
        'success': True,
        'total_students': len(students),
        'today_present': present_count,
        'today_total': len(today_attendance) or len(students)
    })

if __name__ == '__main__':
    app.run(debug=True)
