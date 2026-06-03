import os
import json
import uuid
from functools import wraps
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_for_dev')

# Initialize OpenAI Client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Google Sheets Setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'CREDENTIALS.JSON'
SPREADSHEET_NAME = 'ASWATHAMA_CLASSES_DB' # Or you could identify by ID

# In-memory mock database fallback
MOCK_DB = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def get_db():
    try:
        if os.path.exists(CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            gc = gspread.authorize(creds)
            # You might need to open by url/key if 'ASWATHAMA_CLASSES_DB' is just a placeholder name
            try:
                sheet = gc.open(SPREADSHEET_NAME)
                return sheet
            except gspread.exceptions.SpreadsheetNotFound:
                # Fallback to mock db if the sheet isn't found
                return None
    except Exception as e:
        print(f"Failed to initialize Google Sheets: {e}")
    return None

def fetch_table(table_name):
    db = get_db()
    if db:
        try:
            worksheet = db.worksheet(table_name)
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            print(f"Error fetching from {table_name}: {e}")
            return MOCK_DB.get(table_name, [])
    else:
        return MOCK_DB.get(table_name, [])

def insert_record(table_name, record):
    db = get_db()
    if db:
        try:
            worksheet = db.worksheet(table_name)
            # Get headers to ensure correct order
            headers = worksheet.row_values(1)
            row_data = [record.get(h, '') for h in headers]
            worksheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error inserting into {table_name}: {e}")

    # Mock DB insertion
    if table_name in MOCK_DB:
        MOCK_DB[table_name].append(record)
    return True

def update_record(table_name, record_id, record_data, id_field='id'):
    db = get_db()
    if db:
        try:
            worksheet = db.worksheet(table_name)
            records = worksheet.get_all_records()
            headers = worksheet.row_values(1)
            for i, rec in enumerate(records):
                if str(rec.get(id_field)) == str(record_id):
                    row_index = i + 2 # +1 for header, +1 for 0-index
                    # Update cells individually to avoid race conditions or overwriting whole row incorrectly
                    for key, val in record_data.items():
                        if key in headers:
                            col_index = headers.index(key) + 1
                            worksheet.update_cell(row_index, col_index, val)
                    return True
        except Exception as e:
            print(f"Error updating {table_name}: {e}")

    # Mock DB update
    if table_name in MOCK_DB:
        for i, rec in enumerate(MOCK_DB[table_name]):
            if str(rec.get(id_field)) == str(record_id):
                MOCK_DB[table_name][i].update(record_data)
                return True
    return False

def delete_record(table_name, record_id, id_field='id'):
    db = get_db()
    if db:
        try:
            worksheet = db.worksheet(table_name)
            records = worksheet.get_all_records()
            for i, rec in enumerate(records):
                if str(rec.get(id_field)) == str(record_id):
                    row_index = i + 2
                    worksheet.delete_rows(row_index)
                    return True
        except Exception as e:
            print(f"Error deleting from {table_name}: {e}")

    if table_name in MOCK_DB:
        MOCK_DB[table_name] = [r for r in MOCK_DB[table_name] if str(r.get(id_field)) != str(record_id)]
        return True
    return False


# Utility Decorator for Role-based Access
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized'}), 401
                return redirect(url_for('login'))
            if role and session.get('user_role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden'}), 403
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- AUTHENTICATION ROUTES ---

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

        # In a real app, verify against a database and hash passwords!
        if role == 'teacher' and username == 'admin' and password == 'admin':
            session['user_role'] = 'teacher'
            session['user_id'] = 'teacher_1'
            session['user_name'] = 'Admin Teacher'
            return redirect(url_for('teacher_dashboard'))

        elif role == 'student':
            students = fetch_table('students')
            student = next((s for s in students if str(s.get('roll')) == username and str(s.get('phone')) == password), None)

            # Fallback for demo
            if not student and username == 'student' and password == 'student':
                if students:
                    student = students[0]
                else:
                    # Mock student
                    student = {'id': str(uuid.uuid4()), 'name': 'Demo Student', 'class': '10', 'roll': '1', 'phone': 'student', 'email': 'student@demo.com', 'parent': 'Demo Parent'}

            if student:
                session['user_role'] = 'student'
                session['user_id'] = str(student.get('id'))
                session['user_name'] = student.get('name')
                return redirect(url_for('student_dashboard'))
            else:
                return render_template('login.html', error='Invalid credentials')

        return render_template('login.html', error='Invalid role or credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- TEACHER ROUTES ---

@app.route('/dashboard')
@login_required('teacher')
def teacher_dashboard():
    students = fetch_table('students')
    attendance = fetch_table('attendance')
    videos = fetch_table('videos')
    return render_template('dashboard.html', students=students, attendance=attendance, videos=videos)

@app.route('/students')
@login_required('teacher')
def students_page():
    return render_template('students.html')

@app.route('/attendance')
@login_required('teacher')
def attendance_page():
    return render_template('attendance.html')

@app.route('/videos')
@login_required('teacher')
def videos_page():
    return render_template('videos.html')

@app.route('/subjects')
@login_required('teacher')
def subjects_page():
    return render_template('subjects.html')

@app.route('/announcements')
@login_required('teacher')
def announcements_page():
    return render_template('announcements.html')

@app.route('/ai-tools')
@login_required('teacher')
def ai_tools_page():
    return render_template('ai_tools.html')

# --- STUDENT ROUTES ---

@app.route('/student-dashboard')
@login_required('student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/my-videos')
@login_required('student')
def my_videos_page():
    return render_template('my_videos.html')

@app.route('/attendance-view')
@login_required('student')
def attendance_view_page():
    return render_template('attendance_view.html')

@app.route('/chatbot')
@login_required('student')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/announcements-view')
@login_required('student')
def announcements_view_page():
    return render_template('announcements_view.html')


# --- DATA REST API ENDPOINTS ---

@app.route('/api/students', methods=['GET', 'POST'])
@login_required('teacher')
def api_students():
    if request.method == 'GET':
        students = fetch_table('students')
        return jsonify(students)
    elif request.method == 'POST':
        data = request.json
        data['id'] = str(uuid.uuid4())
        insert_record('students', data)
        return jsonify({'message': 'Student added successfully', 'id': data['id']})

@app.route('/api/students/<student_id>', methods=['PUT', 'DELETE'])
@login_required('teacher')
def api_student_detail(student_id):
    if request.method == 'PUT':
        data = request.json
        update_record('students', student_id, data)
        return jsonify({'message': 'Student updated successfully'})
    elif request.method == 'DELETE':
        delete_record('students', student_id)
        return jsonify({'message': 'Student deleted successfully'})

@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required('teacher')
def api_attendance():
    if request.method == 'GET':
        attendance = fetch_table('attendance')
        return jsonify(attendance)
    elif request.method == 'POST':
        data = request.json
        # Format: {'date': 'YYYY-MM-DD', 'records': [{'student_id': 'id1', 'status': 'present'}, ...]}
        date = data.get('date')
        records = data.get('records', [])
        for rec in records:
            insert_record('attendance', {
                'date': date,
                'student_id': rec.get('student_id'),
                'status': rec.get('status')
            })
        return jsonify({'message': 'Attendance saved successfully'})

@app.route('/api/student/attendance', methods=['GET'])
@login_required('student')
def api_student_attendance():
    student_id = session.get('user_id')
    all_attendance = fetch_table('attendance')
    student_attendance = [a for a in all_attendance if str(a.get('student_id')) == str(student_id)]
    return jsonify(student_attendance)

@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'GET':
        videos = fetch_table('videos')
        return jsonify(videos)
    elif request.method == 'POST':
        if session.get('user_role') != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        data['id'] = str(uuid.uuid4())
        insert_record('videos', data)
        return jsonify({'message': 'Video added successfully'})

@app.route('/api/videos/<video_id>', methods=['DELETE'])
@login_required('teacher')
def api_video_detail(video_id):
    delete_record('videos', video_id)
    return jsonify({'message': 'Video deleted successfully'})

@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required('teacher')
def api_subjects():
    if request.method == 'GET':
        subjects = fetch_table('subjects')
        return jsonify(subjects)
    elif request.method == 'POST':
        data = request.json
        data['id'] = str(uuid.uuid4())
        insert_record('subjects', data)
        return jsonify({'message': 'Subject added successfully'})

@app.route('/api/subjects/<subject_id>', methods=['DELETE'])
@login_required('teacher')
def api_subject_detail(subject_id):
    delete_record('subjects', subject_id)
    return jsonify({'message': 'Subject deleted successfully'})

@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'GET':
        announcements = fetch_table('announcements')
        return jsonify(announcements)
    elif request.method == 'POST':
        if session.get('user_role') != 'teacher':
            return jsonify({'error': 'Forbidden'}), 403
        data = request.json
        data['id'] = str(uuid.uuid4())
        insert_record('announcements', data)
        return jsonify({'message': 'Announcement added successfully'})

@app.route('/api/announcements/<announcement_id>', methods=['DELETE'])
@login_required('teacher')
def api_announcement_detail(announcement_id):
    delete_record('announcements', announcement_id)
    return jsonify({'message': 'Announcement deleted successfully'})

# --- AI REST API ENDPOINTS ---

@app.route('/api/ai/announcement', methods=['POST'])
@login_required('teacher')
def ai_announcement_generator():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    topic = request.json.get('topic')
    system_prompt = "Write a professional coaching class announcement."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'announcement': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/doubt', methods=['POST'])
@login_required('student')
def ai_doubt_solver():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    question = request.json.get('question')
    system_prompt = "Explain this concept in very simple words for a school student. If it's a math question, give a step by step solution."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
@login_required('student')
def ai_study_chatbot():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    message = request.json.get('message')
    history = request.json.get('history', [])
    system_prompt = "You are a friendly tutor. Help the student with concept doubts, exam preparation, and study tips."
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": message})
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return jsonify({'reply': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/attendance', methods=['POST'])
@login_required('teacher')
def ai_attendance_analysis():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    attendance_data = fetch_table('attendance')
    student_data = fetch_table('students')

    # Structure raw data as per memory instruction
    raw_data = {}
    for a in attendance_data:
        sid = str(a.get('student_id'))
        if sid not in raw_data:
            raw_data[sid] = {'present': 0, 'absent': 0}
        if str(a.get('status')).lower() == 'present':
            raw_data[sid]['present'] += 1
        else:
            raw_data[sid]['absent'] += 1

    # Add names for context
    student_map = {str(s.get('id')): s.get('name') for s in student_data}
    context_data = {student_map.get(sid, sid): counts for sid, counts in raw_data.items()}

    system_prompt = "Analyze attendance data and provide insights. Mention which students are irregular, calculate approximate attendance percentages based on the counts, and suggest actions."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context_data)}
            ]
        )
        return jsonify({'analysis': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/video-summary', methods=['POST'])
@login_required('teacher')
def ai_video_summary():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    topic = request.json.get('topic')
    system_prompt = "Generate summary notes for revision based on the following video topic. Include a brief summary and key points."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
@login_required('teacher')
def ai_quiz_generator():
    if not client: return jsonify({'error': 'OpenAI API key not configured'}), 500
    subject = request.json.get('subject')
    topic = request.json.get('topic')
    system_prompt = "Generate 5 MCQ questions with answers for the given subject and topic. Format as JSON with a list of objects containing 'question', 'options' (array), and 'answer'."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Subject: {subject}, Topic: {topic}"}
            ]
        )
        return jsonify({'quiz': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
