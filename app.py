import os
import json
import uuid
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super_secret_key_for_aswathama_classes')

# OpenAI Integration
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    client = None

# Database Initialization (Google Sheets or Mock)
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_FILE = 'CREDENTIALS.JSON'

class MockDB:
    def __init__(self):
        self.data = {
            'students': [
                {'id': 'student-1', 'name': 'John Doe', 'class': '10th', 'roll': '101', 'phone': '1234567890', 'email': 'john@example.com', 'parent': 'Mr. Doe'}
            ],
            'attendance': [],
            'videos': [],
            'subjects': [{'subject_name': 'Maths'}, {'subject_name': 'Science'}],
            'announcements': []
        }

    def get_all_records(self, sheet_name):
        return self.data.get(sheet_name, [])

    def append_row(self, sheet_name, row_data):
        if sheet_name == 'students':
            record = {'id': row_data[0], 'name': row_data[1], 'class': row_data[2], 'roll': row_data[3], 'phone': row_data[4], 'email': row_data[5], 'parent': row_data[6]}
        elif sheet_name == 'attendance':
            record = {'date': row_data[0], 'student_id': row_data[1], 'status': row_data[2]}
        elif sheet_name == 'videos':
            record = {'date': row_data[0], 'subject': row_data[1], 'drive_link': row_data[2]}
        elif sheet_name == 'subjects':
            record = {'subject_name': row_data[0]}
        elif sheet_name == 'announcements':
            record = {'date': row_data[0], 'message': row_data[1]}
        self.data[sheet_name].append(record)

    def update_record(self, sheet_name, id_col, id_val, updated_dict):
        for idx, row in enumerate(self.data[sheet_name]):
            if str(row.get(id_col)) == str(id_val):
                for k, v in updated_dict.items():
                    self.data[sheet_name][idx][k] = v
                break

    def delete_record(self, sheet_name, id_col, id_val):
        self.data[sheet_name] = [r for r in self.data[sheet_name] if str(r.get(id_col)) != str(id_val)]


class SheetsDB:
    def __init__(self, spreadsheet_id, credentials_file):
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self.gc = gspread.authorize(creds)
        self.spreadsheet_id = spreadsheet_id

    def _get_sheet(self, sheet_name):
        try:
            return self.gc.open_by_key(self.spreadsheet_id).worksheet(sheet_name)
        except Exception as e:
            print(f"Error accessing sheet {sheet_name}: {e}")
            return None

    def get_all_records(self, sheet_name):
        sheet = self._get_sheet(sheet_name)
        if sheet:
            return sheet.get_all_records()
        return []

    def append_row(self, sheet_name, row_data):
        sheet = self._get_sheet(sheet_name)
        if sheet:
            sheet.append_row(row_data)

    def update_record(self, sheet_name, id_col, id_val, updated_dict):
        # A simple but inefficient update for Google Sheets.
        sheet = self._get_sheet(sheet_name)
        if not sheet: return
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        for i, row in enumerate(records):
            if str(row.get(id_col)) == str(id_val):
                # +2 because list is 0-indexed and sheet has headers
                for k, v in updated_dict.items():
                    try:
                        col_idx = headers.index(k) + 1
                        sheet.update_cell(i + 2, col_idx, v)
                    except ValueError:
                        pass
                break

    def delete_record(self, sheet_name, id_col, id_val):
        sheet = self._get_sheet(sheet_name)
        if not sheet: return
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get(id_col)) == str(id_val):
                sheet.delete_rows(i + 2)
                break

try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_content = json.load(f)
    if not creds_content or not SPREADSHEET_ID:
        db = MockDB()
        print("Using Mock Database.")
    else:
        db = SheetsDB(SPREADSHEET_ID, CREDENTIALS_FILE)
        print("Using Google Sheets Database.")
except Exception as e:
    db = MockDB()
    print("Using Mock Database due to error:", e)

# Authentication Decorators
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized'}), 401
                return redirect(url_for('login'))
            if role and session['user']['role'] != role:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden'}), 403
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


# Routes: Auth
@app.route('/')
def index():
    if 'user' in session:
        if session['user']['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        role = data.get('role')
        username = data.get('username')
        password = data.get('password')

        if role == 'teacher':
            if username == 'admin' and password == 'admin':
                session['user'] = {'role': 'teacher', 'id': 'teacher-1', 'name': 'Admin'}
                return jsonify({'success': True, 'redirect': url_for('teacher_dashboard')})
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

        elif role == 'student':
            students = db.get_all_records('students')
            student = None
            if username == 'student' and password == 'student':
                if students:
                    student = students[0]
                else:
                    student = {'id': 'fallback-student', 'name': 'Demo Student', 'class': '10', 'roll': '1', 'phone': '0'}
            else:
                for s in students:
                    if str(s.get('roll')) == username and str(s.get('phone')) == password:
                        student = s
                        break

            if student:
                session['user'] = {
                    'role': 'student',
                    'id': student['id'],
                    'name': student['name'],
                    'class': student.get('class')
                }
                return jsonify({'success': True, 'redirect': url_for('student_dashboard')})
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Routes: Teacher HTML
@app.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    return render_template('teacher/dashboard.html')

@app.route('/teacher/students')
@login_required(role='teacher')
def teacher_students():
    return render_template('teacher/students.html')

@app.route('/teacher/attendance')
@login_required(role='teacher')
def teacher_attendance():
    return render_template('teacher/attendance.html')

@app.route('/teacher/videos')
@login_required(role='teacher')
def teacher_videos():
    return render_template('teacher/videos.html')

@app.route('/teacher/subjects')
@login_required(role='teacher')
def teacher_subjects():
    return render_template('teacher/subjects.html')

@app.route('/teacher/announcements')
@login_required(role='teacher')
def teacher_announcements():
    return render_template('teacher/announcements.html')

@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def teacher_ai_tools():
    return render_template('teacher/ai_tools.html')

# Routes: Student HTML
@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    return render_template('student/student_dashboard.html')

@app.route('/student/my_videos')
@login_required(role='student')
def student_my_videos():
    return render_template('student/my_videos.html')

@app.route('/student/attendance')
@login_required(role='student')
def student_attendance_view():
    return render_template('student/attendance_view.html')

@app.route('/student/chatbot')
@login_required(role='student')
def student_chatbot():
    return render_template('student/chatbot.html')

@app.route('/student/announcements')
@login_required(role='student')
def student_announcements():
    return render_template('student/announcements_view.html')


# API: Data
@app.route('/api/students', methods=['GET', 'POST'])
@login_required(role='teacher')
def api_students():
    if request.method == 'GET':
        return jsonify(db.get_all_records('students'))
    elif request.method == 'POST':
        data = request.json
        new_id = str(uuid.uuid4())
        row = [new_id, data.get('name'), data.get('class'), data.get('roll'), data.get('phone'), data.get('email'), data.get('parent')]
        db.append_row('students', row)
        return jsonify({'success': True, 'id': new_id})

@app.route('/api/students/<student_id>', methods=['DELETE', 'PUT'])
@login_required(role='teacher')
def api_student_action(student_id):
    if request.method == 'DELETE':
        db.delete_record('students', 'id', student_id)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.json
        db.update_record('students', 'id', student_id, data)
        return jsonify({'success': True})

@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def api_attendance():
    if request.method == 'GET':
        date = request.args.get('date')
        records = db.get_all_records('attendance')
        if date:
            records = [r for r in records if r.get('date') == date]
        if session['user']['role'] == 'student':
            records = [r for r in records if str(r.get('student_id')) == str(session['user']['id'])]
        return jsonify(records)
    elif request.method == 'POST':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        date = data.get('date')
        records = data.get('records', [])
        # We simulate save by deleting existing for date and appending
        existing = db.get_all_records('attendance')
        for r in existing:
            if r.get('date') == date:
                db.delete_record('attendance', 'date', date) # simplified delete by date
        for rec in records:
            db.append_row('attendance', [date, rec['student_id'], rec['status']])
        return jsonify({'success': True})

@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'GET':
        return jsonify(db.get_all_records('videos'))
    elif request.method == 'POST':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        db.append_row('videos', [data.get('date'), data.get('subject'), data.get('drive_link')])
        return jsonify({'success': True})

@app.route('/api/subjects', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required()
def api_subjects():
    if request.method == 'GET':
        return jsonify(db.get_all_records('subjects'))
    elif request.method == 'POST':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        db.append_row('subjects', [data.get('subject_name')])
        return jsonify({'success': True})
    elif request.method == 'PUT':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        db.update_record('subjects', 'subject_name', old_name, {'subject_name': new_name})
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        subject = request.args.get('subject_name')
        db.delete_record('subjects', 'subject_name', subject)
        return jsonify({'success': True})

@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'GET':
        return jsonify(db.get_all_records('announcements'))
    elif request.method == 'POST':
        if session['user']['role'] != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        date = datetime.now().strftime("%Y-%m-%d")
        db.append_row('announcements', [date, data.get('message')])
        return jsonify({'success': True})

@app.route('/api/stats')
@login_required(role='teacher')
def api_stats():
    students = db.get_all_records('students')
    attendance = db.get_all_records('attendance')
    announcements = db.get_all_records('announcements')
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = [r for r in attendance if r.get('date') == today and r.get('status') == 'Present']

    recent_activity = []
    for a in reversed(announcements[-3:]):
        recent_activity.append(f"Announcement: {a.get('message')[:30]}...")

    return jsonify({
        'total_students': len(students),
        'today_attendance': len(today_attendance),
        'recent_activity': recent_activity
    })

@app.route('/api/today_video')
@login_required(role='student')
def api_today_video():
    videos = db.get_all_records('videos')
    today = datetime.now().strftime("%Y-%m-%d")
    today_vids = [v for v in videos if v.get('date') == today]
    if today_vids:
        return jsonify(today_vids[0])
    return jsonify({})

# AI Endpoints
def ask_ai(system_prompt, user_message):
    if not client:
        return "AI is currently disabled (OPENAI_API_KEY missing)."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

@app.route('/api/ai/doubt', methods=['POST'])
@login_required(role='student')
def ai_doubt():
    question = request.json.get('question')
    prompt = "Explain this concept in very simple words for a school student. If it's a math question, give a step by step solution."
    answer = ask_ai(prompt, question)
    return jsonify({'answer': answer})

@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def ai_chat():
    message = request.json.get('message')
    prompt = "You are a friendly study tutor. Answer questions about concept doubts, exam preparation, and study tips."
    answer = ask_ai(prompt, message)
    return jsonify({'answer': answer})

@app.route('/api/ai/attendance', methods=['POST'])
@login_required(role='teacher')
def ai_attendance_analysis():
    records = db.get_all_records('attendance')
    students = db.get_all_records('students')
    student_map = {str(s['id']): s['name'] for s in students}

    analysis_data = {}
    for r in records:
        sid = str(r.get('student_id'))
        name = student_map.get(sid, sid)
        if name not in analysis_data:
            analysis_data[name] = {'Present': 0, 'Absent': 0}
        status = r.get('status', 'Absent')
        if status in analysis_data[name]:
            analysis_data[name][status] += 1

    prompt = "Analyze attendance data and provide insights. Point out which students are irregular, calculate approximate attendance percentage if possible, and suggest actions."
    data_str = json.dumps(analysis_data)
    answer = ask_ai(prompt, f"Here is the raw attendance count per student: {data_str}")
    return jsonify({'analysis': answer})

@app.route('/api/ai/summary', methods=['POST'])
@login_required(role='teacher')
def ai_summary():
    topic = request.json.get('topic')
    prompt = "Generate summary notes for revision including summary and key points."
    answer = ask_ai(prompt, f"Topic: {topic}")
    return jsonify({'summary': answer})

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz():
    topic = request.json.get('topic')
    prompt = "Generate 5 MCQ questions with answers."
    answer = ask_ai(prompt, f"Subject/Topic: {topic}")
    return jsonify({'quiz': answer})

@app.route('/api/ai/announce', methods=['POST'])
@login_required(role='teacher')
def ai_announce():
    topic = request.json.get('topic')
    prompt = "Write a professional coaching class announcement."
    answer = ask_ai(prompt, topic)
    return jsonify({'announcement': answer})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
