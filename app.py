import os
import json
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')

# Initialize OpenAI
openai_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_key) if openai_key else None

class Database:
    def __init__(self):
        self.mock_mode = False
        self.client = None
        self.sheet = None

        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file('CREDENTIALS.JSON', scopes=scope)
            self.client = gspread.authorize(creds)
            sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Aswathama Classes Database')
            self.sheet = self.client.open(sheet_name)
            print("Connected to Google Sheets successfully.")
        except Exception as e:
            print(f"Failed to connect to Google Sheets. Using mock database fallback. Error: {e}")
            self.mock_mode = True
            self.mock_db = {
                'students': [{'id': 'S001', 'name': 'John Doe', 'class': '10th', 'roll': '1', 'phone': '1234567890', 'email': 'john@example.com', 'parent': 'Jane Doe'}],
                'attendance': [],
                'videos': [{'date': datetime.now().strftime("%Y-%m-%d"), 'subject': 'Mathematics', 'drive_link': 'https://drive.google.com/test'}],
                'subjects': [{'subject_name': 'Mathematics'}, {'subject_name': 'Science'}],
                'announcements': [{'date': datetime.now().strftime("%Y-%m-%d"), 'message': 'Welcome to Aswathama Classes!'}]
            }

    def get_all_records(self, sheet_name):
        if self.mock_mode:
            return self.mock_db.get(sheet_name, [])
        try:
            return self.sheet.worksheet(sheet_name).get_all_records()
        except Exception as e:
            print(f"Error fetching records from {sheet_name}: {e}")
            return []

    def append_row(self, sheet_name, row_data, headers):
        if self.mock_mode:
            row_dict = dict(zip(headers, row_data))
            self.mock_db[sheet_name].append(row_dict)
            return True
        try:
            self.sheet.worksheet(sheet_name).append_row(row_data)
            return True
        except Exception as e:
            print(f"Error appending row to {sheet_name}: {e}")
            return False

    def update_row(self, sheet_name, key_field, key_value, row_data, headers):
        if self.mock_mode:
            new_row_dict = dict(zip(headers, row_data))
            for i, record in enumerate(self.mock_db[sheet_name]):
                if str(record.get(key_field)) == str(key_value):
                    self.mock_db[sheet_name][i] = new_row_dict
                    return True
            return False

        try:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            for i, record in enumerate(records):
                if str(record.get(key_field)) == str(key_value):
                    worksheet.update(f"A{i+2}", [row_data])
                    return True
            return False
        except Exception as e:
            print(f"Error updating row in {sheet_name}: {e}")
            return False

    def delete_row(self, sheet_name, key_field, key_value):
        if self.mock_mode:
            self.mock_db[sheet_name] = [r for r in self.mock_db[sheet_name] if str(r.get(key_field)) != str(key_value)]
            return True
        try:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            for i, record in enumerate(records):
                if str(record.get(key_field)) == str(key_value):
                    worksheet.delete_rows(i+2)
                    return True
            return False
        except Exception as e:
            print(f"Error deleting row in {sheet_name}: {e}")
            return False

    def save_attendance(self, date, records_list):
        if self.mock_mode:
            self.mock_db['attendance'] = [r for r in self.mock_db['attendance'] if r['date'] != date]
            for r in records_list:
                self.mock_db['attendance'].append({'date': date, 'student_id': r['student_id'], 'status': r['status']})
            return True

        try:
            worksheet = self.sheet.worksheet('attendance')
            all_records = worksheet.get_all_records()
            new_records = [r for r in all_records if r['date'] != date]
            for r in records_list:
                new_records.append({'date': date, 'student_id': r['student_id'], 'status': r['status']})

            worksheet.clear()
            worksheet.append_row(['date', 'student_id', 'status'])
            values = [[r['date'], r['student_id'], r['status']] for r in new_records]
            if values:
                worksheet.append_rows(values)
            return True
        except Exception as e:
            print(f"Error saving attendance: {e}")
            return False

db = Database()

def login_required(role=None):
    """
    Custom login required decorator.
    Returns 401 or 403 JSON responses upon authentication failure for /api/ routes.
    """
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized'}), 401
                return redirect(url_for('login'))
            if role and session.get('user_role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Forbidden'}), 403
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def ask_ai(system_prompt, user_content):
    if not client:
        return "OpenAI API key not configured. This is a mock AI response."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"

# ================= VIEWS =================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_role' in session:
        if session['user_role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Teacher Views
@app.route('/teacher/dashboard')
@login_required('teacher')
def teacher_dashboard():
    return render_template('dashboard.html')

@app.route('/teacher/students')
@login_required('teacher')
def students_page():
    return render_template('students.html')

@app.route('/teacher/attendance')
@login_required('teacher')
def attendance_page():
    return render_template('attendance.html')

@app.route('/teacher/videos')
@login_required('teacher')
def videos_page():
    return render_template('videos.html')

@app.route('/teacher/subjects')
@login_required('teacher')
def subjects_page():
    return render_template('subjects.html')

@app.route('/teacher/announcements')
@login_required('teacher')
def announcements_page():
    return render_template('announcements.html')

@app.route('/teacher/ai_tools')
@login_required('teacher')
def ai_tools_page():
    return render_template('ai_tools.html')

# Student Views
@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/student/my_videos')
@login_required('student')
def my_videos_page():
    return render_template('my_videos.html')

@app.route('/student/attendance')
@login_required('student')
def student_attendance_page():
    return render_template('attendance_view.html')

@app.route('/student/chatbot')
@login_required('student')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/student/announcements')
@login_required('student')
def student_announcements_page():
    return render_template('announcements_view.html')

# ================= API ENDPOINTS =================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    role = data.get('role')
    if role == 'teacher':
        username = data.get('username')
        password = data.get('password')
        if username == 'admin' and password == 'admin':
            session['user_role'] = 'teacher'
            session['user_name'] = 'Admin Teacher'
            return jsonify({'success': True, 'redirect': url_for('teacher_dashboard')})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    elif role == 'student':
        student_id = data.get('student_id')
        students = db.get_all_records('students')
        student = next((s for s in students if str(s['id']) == str(student_id)), None)
        if student:
            session['user_role'] = 'student'
            session['user_id'] = str(student['id'])
            session['user_name'] = student['name']
            return jsonify({'success': True, 'redirect': url_for('student_dashboard')})
        return jsonify({'success': False, 'message': 'Student ID not found'}), 401
    return jsonify({'success': False, 'message': 'Invalid role'}), 400

@app.route('/api/dashboard_stats', methods=['GET'])
@login_required('teacher')
def api_dashboard_stats():
    students = db.get_all_records('students')
    attendance = db.get_all_records('attendance')
    today = datetime.now().strftime("%Y-%m-%d")
    today_attendance = [a for a in attendance if a['date'] == today]
    present_count = len([a for a in today_attendance if a['status'].lower() == 'present'])
    return jsonify({
        'success': True,
        'total_students': len(students),
        'today_attendance_percent': round((present_count / len(students) * 100) if students else 0, 1),
        'recent_activity': 'System checked recently.'
    })

# Students CRUD
@app.route('/api/students', methods=['GET'])
@login_required()
def get_students():
    return jsonify({'success': True, 'students': db.get_all_records('students')})

@app.route('/api/students', methods=['POST'])
@login_required('teacher')
def add_student():
    data = request.json
    s_id = data.get('id') or str(uuid.uuid4())[:8]
    row = [s_id, data.get('name'), data.get('class'), data.get('roll'), data.get('phone'), data.get('email'), data.get('parent')]
    success = db.append_row('students', row, ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'])
    return jsonify({'success': success})

@app.route('/api/students/<student_id>', methods=['PUT', 'DELETE'])
@login_required('teacher')
def edit_delete_student(student_id):
    if request.method == 'PUT':
        data = request.json
        row = [student_id, data.get('name'), data.get('class'), data.get('roll'), data.get('phone'), data.get('email'), data.get('parent')]
        success = db.update_row('students', 'id', student_id, row, ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'])
        return jsonify({'success': success})
    elif request.method == 'DELETE':
        success = db.delete_row('students', 'id', student_id)
        return jsonify({'success': success})

# Attendance
@app.route('/api/attendance', methods=['GET'])
@login_required()
def get_attendance():
    date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    all_att = db.get_all_records('attendance')
    records = [a for a in all_att if a['date'] == date]

    # If student, return all their attendance
    if session.get('user_role') == 'student':
        s_id = session.get('user_id')
        records = [a for a in all_att if str(a['student_id']) == s_id]

    return jsonify({'success': True, 'attendance': records})

@app.route('/api/attendance', methods=['POST'])
@login_required('teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])
    success = db.save_attendance(date, records)
    return jsonify({'success': success})

# Videos
@app.route('/api/videos', methods=['GET'])
@login_required()
def get_videos():
    return jsonify({'success': True, 'videos': db.get_all_records('videos')})

@app.route('/api/videos', methods=['POST'])
@login_required('teacher')
def add_video():
    data = request.json
    row = [data.get('date'), data.get('subject'), data.get('drive_link')]
    success = db.append_row('videos', row, ['date', 'subject', 'drive_link'])
    return jsonify({'success': success})

# Subjects
@app.route('/api/subjects', methods=['GET'])
@login_required()
def get_subjects():
    return jsonify({'success': True, 'subjects': db.get_all_records('subjects')})

@app.route('/api/subjects', methods=['POST'])
@login_required('teacher')
def add_subject():
    data = request.json
    row = [data.get('subject_name')]
    success = db.append_row('subjects', row, ['subject_name'])
    return jsonify({'success': success})

@app.route('/api/subjects/<subject_name>', methods=['DELETE'])
@login_required('teacher')
def delete_subject(subject_name):
    success = db.delete_row('subjects', 'subject_name', subject_name)
    return jsonify({'success': success})

# Announcements
@app.route('/api/announcements', methods=['GET'])
@login_required()
def get_announcements():
    return jsonify({'success': True, 'announcements': db.get_all_records('announcements')})

@app.route('/api/announcements', methods=['POST'])
@login_required('teacher')
def add_announcement():
    data = request.json
    row = [data.get('date', datetime.now().strftime("%Y-%m-%d")), data.get('message')]
    success = db.append_row('announcements', row, ['date', 'message'])
    return jsonify({'success': success})

# ================= AI FEATURES =================

@app.route('/api/ai/doubt_solver', methods=['POST'])
@login_required('student')
def api_doubt_solver():
    question = request.json.get('question', '')
    prompt = "Explain this concept in very simple words for a school student. If it is a math question, give step by step solution."
    answer = ask_ai(prompt, question)
    return jsonify({'success': True, 'answer': answer})

@app.route('/api/ai/chatbot', methods=['POST'])
@login_required('student')
def api_chatbot():
    message = request.json.get('message', '')
    prompt = "You are a friendly tutor chatbot. Answer the student's questions regarding concept doubts, exam preparation, or study tips."
    answer = ask_ai(prompt, message)
    return jsonify({'success': True, 'answer': answer})

@app.route('/api/ai/attendance_analysis', methods=['POST'])
@login_required('teacher')
def api_attendance_analysis():
    records = db.get_all_records('attendance')
    structured = {}
    for r in records:
        sid = str(r.get('student_id'))
        if not sid: continue
        if sid not in structured:
            structured[sid] = {'present': 0, 'absent': 0}
        status = r.get('status', '').lower()
        if status == 'present':
            structured[sid]['present'] += 1
        elif status == 'absent':
            structured[sid]['absent'] += 1

    msg = f"Raw attendance data: {json.dumps(structured)}"
    prompt = "Analyze attendance data and provide insights. Summarize which students are irregular, their attendance percentage, and suggest actions."
    answer = ask_ai(prompt, msg)
    return jsonify({'success': True, 'answer': answer})

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required('teacher')
def api_video_summary():
    topic = request.json.get('topic', '')
    prompt = "Generate summary notes for revision, including key points."
    answer = ask_ai(prompt, topic)
    return jsonify({'success': True, 'answer': answer})

@app.route('/api/ai/quiz_generator', methods=['POST'])
@login_required('teacher')
def api_quiz_generator():
    topic = request.json.get('topic', '')
    prompt = "Generate 5 MCQ questions with answers on the provided topic. Return the questions in a readable format."
    answer = ask_ai(prompt, topic)
    return jsonify({'success': True, 'answer': answer})

@app.route('/api/ai/generate_announcement', methods=['POST'])
@login_required('teacher')
def api_generate_announcement():
    topic = request.json.get('topic', '')
    prompt = "Write a professional coaching class announcement."
    answer = ask_ai(prompt, topic)
    return jsonify({'success': True, 'answer': answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
