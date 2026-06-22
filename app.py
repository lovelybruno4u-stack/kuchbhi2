import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_for_dev')
app.permanent_session_lifetime = timedelta(days=365)

# OpenAI Client Setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets Setup
def get_gspread_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        credentials = Credentials.from_service_account_file('CREDENTIALS.JSON', scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Mock DB Mode: Failed to load Google Credentials. Using mock fallback. ({e})")
        return None

def get_google_sheet(sheet_name):
    gc = get_gspread_client()
    if not gc:
        return None

    try:
        sheet_url = os.getenv('SHEET_URL')
        sh = gc.open_by_url(sheet_url)
    except Exception as e:
        print(f"Error accessing spreadsheet via URL: {e}")
        return None

    try:
        return sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return None

# MOCK DB Fallback (In-memory dict)
MOCK_DB = {
    'students': [
        {'id': str(uuid.uuid4()), 'name': 'John Doe', 'class': '10', 'roll': '101', 'phone': '1234567890', 'email': 'john@example.com', 'parent': 'Mr. Doe'}
    ],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def get_data_from_sheet(sheet_name):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        return sheet.get_all_records()
    return MOCK_DB.get(sheet_name, [])


def update_in_sheet(sheet_name, row_id, new_row_data):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        records = sheet.get_all_records()
        for i, row in enumerate(records, start=2): # +2 for header and 0-index
            if str(row.get('id', '')) == str(row_id) or str(row.get('subject_name', '')) == str(row_id):
                # Update cells
                cell_list = sheet.range(f'A{i}:G{i}' if sheet_name == 'students' else f'A{i}:A{i}')
                for cell, val in zip(cell_list, new_row_data):
                    cell.value = val
                sheet.update_cells(cell_list)
                return True
    else:
        # Mock DB
        if sheet_name in MOCK_DB:
            for item in MOCK_DB[sheet_name]:
                if str(item.get('id', '')) == str(row_id) or str(item.get('subject_name', '')) == str(row_id):
                    # update logic for mock
                    keys = ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'] if sheet_name == 'students' else ['subject_name']
                    item.update(dict(zip(keys, new_row_data)))
                    return True
    return False

def delete_from_sheet(sheet_name, row_id):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        records = sheet.get_all_records()
        for i, row in enumerate(records, start=2):
            if str(row.get('id', '')) == str(row_id) or str(row.get('subject_name', '')) == str(row_id):
                sheet.delete_rows(i)
                return True
    else:
        if sheet_name in MOCK_DB:
            MOCK_DB[sheet_name] = [item for item in MOCK_DB[sheet_name] if str(item.get('id', '')) != str(row_id) and str(item.get('subject_name', '')) != str(row_id)]
            return True
    return False

def append_to_sheet(sheet_name, row_data):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        sheet.append_row(row_data)
    else:
        # Map row_data list to dict based on mock DB schema for 'students' primarily, or general fallback
        if sheet_name == 'students':
            keys = ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent']
            MOCK_DB[sheet_name].append(dict(zip(keys, row_data)))
        elif sheet_name == 'attendance':
             keys = ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated']
             MOCK_DB[sheet_name].append(dict(zip(keys, row_data)))
        elif sheet_name == 'videos':
            keys = ['date', 'subject', 'drive_link']
            MOCK_DB[sheet_name].append(dict(zip(keys, row_data)))
        elif sheet_name == 'subjects':
            keys = ['subject_name']
            MOCK_DB[sheet_name].append(dict(zip(keys, row_data)))
        elif sheet_name == 'announcements':
            keys = ['date', 'message']
            MOCK_DB[sheet_name].append(dict(zip(keys, row_data)))


# Auth Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'role' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'teacher':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden: Teacher access required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'student':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden: Student access required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# ROUTES: AUTHENTICATION
# ==========================================

@app.route('/')
def index():
    if 'role' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'teacher':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == 'admin' and password == 'admin':
                session['role'] = 'teacher'
                session['user_id'] = 'teacher_admin'
                return redirect(url_for('teacher_dashboard'))
            return render_template('login.html', error="Invalid teacher credentials")

        elif role == 'student':
            roll = request.form.get('roll')
            phone = request.form.get('phone')

            # Simple fallback for demo
            if roll == 'student' and phone == 'student':
                students = get_data_from_sheet('students')
                if students:
                     session['user_id'] = str(students[0].get('id', 'mock_student_id'))
                     session['name'] = students[0].get('name', 'Demo Student')
                else:
                     session['user_id'] = 'mock_student_id'
                     session['name'] = 'Demo Student'
                session['role'] = 'student'
                return redirect(url_for('student_dashboard'))

            students = get_data_from_sheet('students')
            for student in students:
                if str(student.get('roll')) == str(roll) and str(student.get('phone')) == str(phone):
                    session['role'] = 'student'
                    session['user_id'] = str(student.get('id'))
                    session['name'] = student.get('name')
                    return redirect(url_for('student_dashboard'))
            return render_template('login.html', error="Invalid student credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==========================================
# ROUTES: TEACHER PAGES
# ==========================================

@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    students = get_data_from_sheet('students')
    attendance = get_data_from_sheet('attendance')

    total_students = len(students)
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = [a for a in attendance if a.get('date') == today and a.get('status') == 'present']

    return render_template('dashboard.html',
                           total_students=total_students,
                           present_today=len(today_attendance))

@app.route('/teacher/students')
@teacher_required
def teacher_students():
    return render_template('students.html')

@app.route('/teacher/attendance')
@teacher_required
def teacher_attendance():
    return render_template('attendance.html')

@app.route('/teacher/videos')
@teacher_required
def teacher_videos():
    return render_template('videos.html')

@app.route('/teacher/subjects')
@teacher_required
def teacher_subjects():
    return render_template('subjects.html')

@app.route('/teacher/announcements')
@teacher_required
def teacher_announcements():
    return render_template('announcements.html')

@app.route('/teacher/ai_tools')
@teacher_required
def teacher_ai_tools():
    return render_template('ai_tools.html')


# ==========================================
# ROUTES: STUDENT PAGES
# ==========================================

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/student/videos')
@student_required
def student_my_videos():
    return render_template('my_videos.html')

@app.route('/student/attendance')
@student_required
def student_attendance_view():
    return render_template('attendance_view.html')

@app.route('/student/chatbot')
@student_required
def student_chatbot():
    return render_template('chatbot.html')

@app.route('/student/announcements')
@student_required
def student_announcements_view():
    return render_template('announcements_view.html')


# ==========================================
# API ROUTES: DATA MANAGEMENT
# ==========================================

@app.route('/api/students', methods=['GET', 'POST', 'PUT', 'DELETE'])
@teacher_required
def api_students():
    if request.method == 'GET':
        students = get_data_from_sheet('students')
        return jsonify({'success': True, 'data': students})

    elif request.method == 'POST':
        data = request.json
        new_id = str(uuid.uuid4())
        row = [
            new_id,
            data.get('name'),
            data.get('class'),
            data.get('roll'),
            data.get('phone'),
            data.get('email'),
            data.get('parent')
        ]
        append_to_sheet('students', row)
        return jsonify({'success': True, 'message': 'Student added successfully'})

    elif request.method == 'PUT':
        data = request.json
        row_id = data.get('id')
        row = [
            row_id,
            data.get('name'),
            data.get('class'),
            data.get('roll'),
            data.get('phone'),
            data.get('email'),
            data.get('parent')
        ]
        update_in_sheet('students', row_id, row)
        return jsonify({'success': True, 'message': 'Student updated successfully'})

    elif request.method == 'DELETE':
        data = request.json
        row_id = data.get('id')
        delete_from_sheet('students', row_id)
        return jsonify({'success': True, 'message': 'Student deleted successfully'})

@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required
def api_attendance():
    if request.method == 'GET':
        date_str = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        all_attendance = get_data_from_sheet('attendance')
        records = [a for a in all_attendance if str(a.get('date')) == str(date_str)]

        # Security: Filter data for student role
        if session.get('role') == 'student':
            student_id = session.get('user_id')
            records = [r for r in records if str(r.get('student_id')) == str(student_id)]

        return jsonify({'success': True, 'data': records})

    elif request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        date_str = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        records = data.get('records', []) # list of dicts: {student_id, student_name, class, status}

        # Simplified: in a real app we'd update existing rows. For now, just appending or mock updating.
        for rec in records:
            row = [
                rec.get('student_id'),
                rec.get('student_name'),
                rec.get('class_name', ''),
                date_str,
                rec.get('status'),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            append_to_sheet('attendance', row)

        return jsonify({'success': True, 'message': 'Attendance saved'})

@app.route('/api/videos', methods=['GET', 'POST'])
@login_required
def api_videos():
    if request.method == 'GET':
        videos = get_data_from_sheet('videos')
        return jsonify({'success': True, 'data': videos})

    elif request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        row = [
            data.get('date'),
            data.get('subject'),
            data.get('drive_link')
        ]
        append_to_sheet('videos', row)
        return jsonify({'success': True, 'message': 'Video added successfully'})

@app.route('/api/subjects', methods=['GET', 'POST', 'PUT', 'DELETE'])
@teacher_required
def api_subjects():
    if request.method == 'GET':
        subjects = get_data_from_sheet('subjects')
        return jsonify({'success': True, 'data': subjects})

    elif request.method == 'POST':
        data = request.json
        row = [data.get('subject_name')]
        append_to_sheet('subjects', row)
        return jsonify({'success': True, 'message': 'Subject added'})

    elif request.method == 'PUT':
        data = request.json
        old_name = data.get('old_name')
        new_name = data.get('subject_name')
        update_in_sheet('subjects', old_name, [new_name])
        return jsonify({'success': True, 'message': 'Subject updated'})

    elif request.method == 'DELETE':
        data = request.json
        name = data.get('subject_name')
        delete_from_sheet('subjects', name)
        return jsonify({'success': True, 'message': 'Subject deleted'})

@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required
def api_announcements():
    if request.method == 'GET':
        announcements = get_data_from_sheet('announcements')
        return jsonify({'success': True, 'data': announcements})

    elif request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        row = [
            datetime.now().strftime("%Y-%m-%d"),
            data.get('message')
        ]
        append_to_sheet('announcements', row)
        return jsonify({'success': True, 'message': 'Announcement saved'})


# ==========================================
# API ROUTES: AI INTEGRATIONS
# ==========================================

@app.route('/api/ai/doubt', methods=['POST'])
@student_required
def ai_doubt_solver():
    data = request.json
    question = data.get('question')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution."},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({'success': True, 'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/chat', methods=['POST'])
@student_required
def ai_study_chatbot():
    data = request.json
    chat_history = data.get('history', [])
    new_message = data.get('message')

    messages = [{"role": "system", "content": "You are a friendly, helpful tutor for a school student. Help with concept doubts, exam prep, and study tips."}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": new_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return jsonify({'success': True, 'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/attendance', methods=['POST'])
@teacher_required
def ai_attendance_analysis():
    # Pass raw attendance data to AI
    attendance_data = get_data_from_sheet('attendance')

    # We aggregate a simple dictionary for the AI prompt
    summary_data = {}
    for a in attendance_data:
        sid = a.get('student_id')
        if not sid: continue
        if sid not in summary_data:
            summary_data[sid] = {'present': 0, 'absent': 0, 'name': a.get('student_name', sid)}

        status = str(a.get('status')).lower()
        if status == 'present':
            summary_data[sid]['present'] += 1
        elif status == 'absent':
            summary_data[sid]['absent'] += 1

    prompt = f"Analyze attendance data and provide insights. Data: {json.dumps(summary_data)}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze the raw attendance counts. Identify irregular students, calculate percentages, and suggest actions in a clean, short summary."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({'success': True, 'analysis': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/video_summary', methods=['POST'])
@teacher_required
def ai_video_summary():
    data = request.json
    topic = data.get('topic')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate summary notes for revision including a brief summary and key points."},
                {"role": "user", "content": f"Topic: {topic}"}
            ]
        )
        return jsonify({'success': True, 'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/quiz', methods=['POST'])
@teacher_required
def ai_quiz_generator():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate 5 MCQ questions with answers."},
                {"role": "user", "content": f"Subject: {subject}. Topic: {topic}. Output format should be clear text."}
            ]
        )
        return jsonify({'success': True, 'quiz': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/announcement', methods=['POST'])
@teacher_required
def ai_announcement():
    data = request.json
    topic = data.get('topic')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Write a professional coaching class announcement."},
                {"role": "user", "content": f"Write an announcement about: {topic}"}
            ]
        )
        return jsonify({'success': True, 'announcement': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
