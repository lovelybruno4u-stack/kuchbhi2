import os
import json
import uuid
from functools import wraps
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Use a default secret key for development if not in env
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-dev-secret-key")

# --- Database Setup (Google Sheets with Mock Fallback) ---
# Check if valid credentials exist
USE_MOCK_DB = True
SHEET_ID = os.getenv("GOOGLE_SHEET_ID") # Keep flexible if user provides via env

try:
    if os.path.exists("CREDENTIALS.JSON"):
        with open("CREDENTIALS.JSON", "r") as f:
            cred_data = json.load(f)
            # Basic validation to see if it's an actual service account key, not an empty dict
            if "type" in cred_data and cred_data["type"] == "service_account":
                scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                creds = Credentials.from_service_account_file("CREDENTIALS.JSON", scopes=scopes)
                client = gspread.authorize(creds)

                # We need a spreadsheet to connect to. In a real scenario, this would be provided.
                # For this implementation, we will fall back to mock if SHEET_ID is not provided
                # or if we can't open it.
                if SHEET_ID:
                    sheet = client.open_by_key(SHEET_ID)
                    USE_MOCK_DB = False
                    print("Connected to Google Sheets successfully.")
                else:
                    print("GOOGLE_SHEET_ID not provided. Using Mock DB.")
            else:
                 print("CREDENTIALS.JSON is empty or invalid. Using Mock DB.")
    else:
        print("CREDENTIALS.JSON not found. Using Mock DB.")
except Exception as e:
    print(f"Failed to initialize Google Sheets: {e}. Using Mock DB.")

# --- Mock Database Structure ---
mock_db = {
    "students": [
        {"id": "std-001", "name": "student", "class": "10th", "roll": "101", "phone": "student", "email": "student@example.com", "parent": "Parent1"},
        {"id": "std-002", "name": "Alice Smith", "class": "10th", "roll": "102", "phone": "9876543210", "email": "alice@example.com", "parent": "Parent2"},
    ],
    "attendance": [
        {"date": "2023-10-25", "student_id": "std-001", "status": "present"},
        {"date": "2023-10-25", "student_id": "std-002", "status": "absent"},
    ],
    "videos": [
        {"date": "2023-10-24", "subject": "Math", "drive_link": "https://drive.google.com/math"}
    ],
    "subjects": [
        {"subject_name": "Math"},
        {"subject_name": "Science"}
    ],
    "announcements": [
        {"date": "2023-10-25", "message": "Tomorrow is a holiday!"}
    ]
}

# Helper to interact with DB
def get_db_records(sheet_name):
    if USE_MOCK_DB:
        return mock_db.get(sheet_name, [])
    else:
        try:
            worksheet = sheet.worksheet(sheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"Error reading {sheet_name}: {e}")
            return []

def append_db_record(sheet_name, data_list):
    if USE_MOCK_DB:
        # Convert list to dict based on sheet columns
        cols = {
            "students": ["id", "name", "class", "roll", "phone", "email", "parent"],
            "attendance": ["date", "student_id", "status"],
            "videos": ["date", "subject", "drive_link"],
            "subjects": ["subject_name"],
            "announcements": ["date", "message"]
        }
        if sheet_name in cols:
            record = dict(zip(cols[sheet_name], data_list))
            mock_db[sheet_name].append(record)
    else:
        try:
            worksheet = sheet.worksheet(sheet_name)
            worksheet.append_row(data_list)
        except Exception as e:
            print(f"Error writing to {sheet_name}: {e}")

# Note: Deleting/Updating in gspread is complex as we need to find rows.
# For mock DB, we will implement simple updates.
def update_db_record_mock(sheet_name, record_id_col, record_id_val, new_data_dict):
    if USE_MOCK_DB:
         for item in mock_db.get(sheet_name, []):
             if str(item.get(record_id_col)) == str(record_id_val):
                 item.update(new_data_dict)
                 return True
    return False

def delete_db_record_mock(sheet_name, record_id_col, record_id_val):
    if USE_MOCK_DB:
        original_len = len(mock_db.get(sheet_name, []))
        mock_db[sheet_name] = [item for item in mock_db.get(sheet_name, []) if str(item.get(record_id_col)) != str(record_id_val)]
        return len(mock_db[sheet_name]) < original_len
    return False


# --- Authentication System ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            # Check if it's an API route
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            # Otherwise redirect to login
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'teacher':
            if request.path.startswith('/api/'):
                return jsonify({"error": "Forbidden"}), 403
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# View Routes for Auth
@app.route('/')
def index():
    if 'role' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard_page'))
        else:
            return redirect(url_for('student_dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    role = data.get('role')
    username = data.get('username') # for teacher
    password = data.get('password') # for teacher
    roll_no = data.get('roll_no')   # for student
    phone = data.get('phone')       # for student

    if role == 'teacher':
        if username == 'admin' and password == 'admin':
            session['user_id'] = 'teacher-admin'
            session['role'] = 'teacher'
            session['name'] = 'Admin Teacher'
            return jsonify({"success": True, "redirect": "/dashboard"})
        else:
            return jsonify({"success": False, "error": "Invalid teacher credentials."}), 401

    elif role == 'student':
        # Demo mode / Fallback
        if roll_no == 'student' and phone == 'student':
             students = get_db_records('students')
             if students:
                 first_student = students[0]
                 session['user_id'] = first_student['id']
                 session['role'] = 'student'
                 session['name'] = first_student['name']
                 return jsonify({"success": True, "redirect": "/student_dashboard"})
             else:
                  return jsonify({"success": False, "error": "No students found in DB."}), 404

        students = get_db_records('students')
        for student in students:
            if str(student.get('roll')) == str(roll_no) and str(student.get('phone')) == str(phone):
                session['user_id'] = student.get('id')
                session['role'] = 'student'
                session['name'] = student.get('name')
                return jsonify({"success": True, "redirect": "/student_dashboard"})

        return jsonify({"success": False, "error": "Invalid student credentials."}), 401

    return jsonify({"success": False, "error": "Invalid role."}), 400

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True})

# --- Teacher Views ---
@app.route('/dashboard')
@teacher_required
def teacher_dashboard_page():
    return render_template('dashboard.html')

@app.route('/students')
@teacher_required
def students_page():
    return render_template('students.html')

@app.route('/attendance')
@teacher_required
def attendance_page():
    return render_template('attendance.html')

@app.route('/videos')
@teacher_required
def videos_page():
    return render_template('videos.html')

@app.route('/subjects')
@teacher_required
def subjects_page():
    return render_template('subjects.html')

@app.route('/announcements')
@teacher_required
def announcements_page():
    return render_template('announcements.html')

@app.route('/ai_tools')
@teacher_required
def ai_tools_page():
    return render_template('ai_tools.html')

# --- Student Views ---
@app.route('/student_dashboard')
@login_required
def student_dashboard_page():
    if session.get('role') != 'student':
        return redirect(url_for('teacher_dashboard_page'))
    return render_template('student_dashboard.html')

@app.route('/my_videos')
@login_required
def my_videos_page():
    return render_template('my_videos.html')

@app.route('/attendance_view')
@login_required
def attendance_view_page():
    return render_template('attendance_view.html')

@app.route('/chatbot')
@login_required
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/announcements_view')
@login_required
def announcements_view_page():
    return render_template('announcements_view.html')


# --- CRUD APIs (Part 1: Students & Attendance) ---
@app.route('/api/students', methods=['GET', 'POST'])
@login_required
def handle_students():
    if request.method == 'GET':
        students = get_db_records('students')
        return jsonify(students)

    if request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({"error": "Forbidden"}), 403
        data = request.json
        new_id = str(uuid.uuid4())
        record = [
            new_id,
            data.get('name'),
            data.get('class'),
            data.get('roll'),
            data.get('phone'),
            data.get('email'),
            data.get('parent')
        ]
        append_db_record('students', record)
        return jsonify({"success": True, "id": new_id})

@app.route('/api/students/<student_id>', methods=['PUT', 'DELETE'])
@teacher_required
def handle_student_item(student_id):
    if request.method == 'PUT':
        data = request.json
        success = update_db_record_mock('students', 'id', student_id, data)
        return jsonify({"success": success})

    if request.method == 'DELETE':
        success = delete_db_record_mock('students', 'id', student_id)
        return jsonify({"success": success})

@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required
def handle_attendance():
    if request.method == 'GET':
        attendance = get_db_records('attendance')
        # If student, only return their attendance
        if session.get('role') == 'student':
             attendance = [a for a in attendance if str(a.get('student_id')) == session.get('user_id')]
        return jsonify(attendance)

    if request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({"error": "Forbidden"}), 403
        data = request.json
        date = data.get('date')
        records = data.get('records', []) # list of {student_id, status}

        for rec in records:
            # We skip complex upsert logic for mock/gsheets in this demo, just append
            append_db_record('attendance', [date, rec.get('student_id'), rec.get('status')])

        return jsonify({"success": True})


# --- CRUD APIs (Part 2: Videos, Subjects, Announcements) ---
@app.route('/api/videos', methods=['GET', 'POST'])
@login_required
def handle_videos():
    if request.method == 'GET':
        videos = get_db_records('videos')
        return jsonify(videos)

    if request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({"error": "Forbidden"}), 403
        data = request.json
        record = [
            data.get('date'),
            data.get('subject'),
            data.get('drive_link')
        ]
        append_db_record('videos', record)
        return jsonify({"success": True})

@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required
def handle_subjects():
    if request.method == 'GET':
        subjects = get_db_records('subjects')
        return jsonify(subjects)

    if request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({"error": "Forbidden"}), 403
        data = request.json
        record = [
            data.get('subject_name')
        ]
        append_db_record('subjects', record)
        return jsonify({"success": True})

@app.route('/api/subjects/<subject_name>', methods=['DELETE'])
@teacher_required
def handle_subject_item(subject_name):
    success = delete_db_record_mock('subjects', 'subject_name', subject_name)
    return jsonify({"success": success})


@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required
def handle_announcements():
    if request.method == 'GET':
        announcements = get_db_records('announcements')
        return jsonify(announcements)

    if request.method == 'POST':
        if session.get('role') != 'teacher':
             return jsonify({"error": "Forbidden"}), 403
        data = request.json
        record = [
            data.get('date'),
            data.get('message')
        ]
        append_db_record('announcements', record)
        return jsonify({"success": True})


# --- AI Integration Endpoints ---
# Memory constraint: Consolidated under /api/ai/ prefix, using gpt-4o-mini
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI()

def call_openai(messages):
    if not openai_client:
        return {"error": "OpenAI API key not configured"}
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return {"content": response.choices[0].message.content}
    except Exception as e:
        print(f"OpenAI error: {e}")
        return {"error": str(e)}

@app.route('/api/ai/doubt_solver', methods=['POST'])
@login_required
def ai_doubt_solver():
    data = request.json
    question = data.get('question', '')

    system_prompt = "Explain this concept in very simple words for a school student. If it's a math question, give a step by step solution."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    result = call_openai(messages)
    return jsonify(result)

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def ai_study_chatbot():
    data = request.json
    history = data.get('history', [])
    new_message = data.get('message', '')

    system_prompt = "You are a friendly tutor. Help the student with concept doubts, exam preparation, and study tips."
    messages = [{"role": "system", "content": system_prompt}]

    # Add history
    for msg in history:
        messages.append({"role": msg.get('role'), "content": msg.get('content')})

    messages.append({"role": "user", "content": new_message})

    result = call_openai(messages)
    return jsonify(result)

@app.route('/api/ai/attendance', methods=['POST'])
@teacher_required
def ai_attendance_analysis():
    # Fetch RAW data and supply it to OpenAI
    attendance_data = get_db_records('attendance')

    # Process into a dictionary of student_id mapped to present/absent counts
    student_stats = {}
    for record in attendance_data:
        sid = record.get('student_id')
        status = record.get('status', '').lower()
        if sid not in student_stats:
            student_stats[sid] = {"present": 0, "absent": 0}
        if status == 'present':
            student_stats[sid]["present"] += 1
        elif status == 'absent':
            student_stats[sid]["absent"] += 1

    # Include student names for better context
    students = get_db_records('students')
    student_map = {str(s.get('id')): s.get('name') for s in students}

    raw_data_str = "Attendance Data:\n"
    for sid, stats in student_stats.items():
        name = student_map.get(str(sid), f"Unknown ({sid})")
        raw_data_str += f"Student: {name}, Present: {stats['present']}, Absent: {stats['absent']}\n"

    system_prompt = "Analyze attendance data and provide insights. State which students are irregular, calculate attendance percentage, and suggest actions."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_data_str}
    ]

    result = call_openai(messages)
    return jsonify(result)

@app.route('/api/ai/video_summary', methods=['POST'])
@teacher_required
def ai_video_summary():
    data = request.json
    topic = data.get('topic', '')

    system_prompt = "Generate summary notes for revision including a summary and key points based on the provided video topic."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Topic: {topic}"}
    ]

    result = call_openai(messages)
    return jsonify(result)

@app.route('/api/ai/quiz', methods=['POST'])
@teacher_required
def ai_quiz_generator():
    data = request.json
    subject = data.get('subject', '')
    topic = data.get('topic', '')

    system_prompt = "Generate 5 MCQ questions with answers for the given subject and topic. Format as clear text."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Subject: {subject}, Topic: {topic}"}
    ]

    result = call_openai(messages)
    return jsonify(result)

@app.route('/api/ai/announcement', methods=['POST'])
@teacher_required
def ai_announcement():
    data = request.json
    prompt_text = data.get('prompt', '')

    system_prompt = "Write a professional coaching class announcement based on the user's prompt."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_text}
    ]

    result = call_openai(messages)
    return jsonify(result)

# Need to keep this at bottom as requested
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
