import os
import json
import time
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import traceback

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key_fallback')

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
CREDENTIALS_FILE = 'CREDENTIALS.JSON'
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

# --- Mock DB Fallback ---
MOCK_DB = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def get_gspread_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    try:
        if GOOGLE_CREDENTIALS_JSON:
            creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        elif os.path.exists(CREDENTIALS_FILE) and os.path.getsize(CREDENTIALS_FILE) > 10:
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        else:
            return None # Use mock DB
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error authenticating with Google: {e}")
        return None

def get_sheet_records(sheet_name):
    gc = get_gspread_client()
    if gc and SPREADSHEET_ID:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            ws = sh.worksheet(sheet_name)
            return ws.get_all_records()
        except Exception as e:
            print(f"Error reading from Google Sheets ({sheet_name}): {e}")
            return MOCK_DB.get(sheet_name, [])
    return MOCK_DB.get(sheet_name, [])

def append_sheet_row(sheet_name, row_values):
    gc = get_gspread_client()
    if gc and SPREADSHEET_ID:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            ws = sh.worksheet(sheet_name)
            ws.append_row(row_values)
            return True
        except Exception as e:
            print(f"Error writing to Google Sheets ({sheet_name}): {e}")
            return False
    else:
        # Update Mock DB
        headers_map = {
            'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'],
            'attendance': ['date', 'student_id', 'status'],
            'videos': ['date', 'subject', 'drive_link'],
            'subjects': ['subject_name'],
            'announcements': ['date', 'message']
        }
        headers = headers_map.get(sheet_name, [])
        record = dict(zip(headers, row_values))
        if sheet_name in MOCK_DB:
            MOCK_DB[sheet_name].append(record)
        return True

def delete_sheet_row(sheet_name, id_col_name, row_id):
    gc = get_gspread_client()
    if gc and SPREADSHEET_ID:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            ws = sh.worksheet(sheet_name)
            records = ws.get_all_records()
            for index, record in enumerate(records):
                if str(record.get(id_col_name, '')) == str(row_id):
                    ws.delete_rows(index + 2)
                    return True
        except Exception as e:
            print(f"Error deleting from Google Sheets ({sheet_name}): {e}")
            return False
    else:
        if sheet_name in MOCK_DB:
            MOCK_DB[sheet_name] = [r for r in MOCK_DB[sheet_name] if str(r.get(id_col_name)) != str(row_id)]
        return True

# --- Auth Decorators ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized', 'success': False}), 401
                return redirect(url_for('login_page'))
            if role and session['user_role'] != role:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden', 'success': False}), 403
                return redirect(url_for('login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- UI Routes ---
@app.route('/')
def index():
    if 'user_role' in session:
        if session['user_role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = request.json
        role = data.get('role')
        if role == 'teacher':
            # Simple static teacher password for demo purposes
            if data.get('password') == 'admin123':
                session['user_role'] = 'teacher'
                return jsonify({'success': True, 'redirect': url_for('teacher_dashboard')})
            return jsonify({'success': False, 'error': 'Invalid credentials'})
        elif role == 'student':
            student_id = data.get('student_id')
            students = get_sheet_records('students')
            for student in students:
                if str(student.get('id')) == str(student_id):
                    session['user_role'] = 'student'
                    session['student_id'] = student_id
                    session['student_name'] = student.get('name')
                    return jsonify({'success': True, 'redirect': url_for('student_dashboard')})
            return jsonify({'success': False, 'error': 'Student ID not found'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# Teacher Pages
@app.route('/teacher')
@login_required('teacher')
def teacher_dashboard(): return render_template('dashboard.html')

@app.route('/teacher/students')
@login_required('teacher')
def teacher_students(): return render_template('students.html')

@app.route('/teacher/attendance')
@login_required('teacher')
def teacher_attendance(): return render_template('attendance.html')

@app.route('/teacher/videos')
@login_required('teacher')
def teacher_videos(): return render_template('videos.html')

@app.route('/teacher/subjects')
@login_required('teacher')
def teacher_subjects(): return render_template('subjects.html')

@app.route('/teacher/announcements')
@login_required('teacher')
def teacher_announcements(): return render_template('announcements.html')

@app.route('/teacher/ai-tools')
@login_required('teacher')
def teacher_ai_tools(): return render_template('ai_tools.html')

# Student Pages
@app.route('/student')
@login_required('student')
def student_dashboard(): return render_template('student_dashboard.html')

@app.route('/student/videos')
@login_required('student')
def student_videos(): return render_template('my_videos.html')

@app.route('/student/attendance')
@login_required('student')
def student_attendance(): return render_template('attendance_view.html')

@app.route('/student/chatbot')
@login_required('student')
def student_chatbot(): return render_template('chatbot.html')

@app.route('/student/announcements')
@login_required('student')
def student_announcements(): return render_template('announcements_view.html')


# --- API Routes ---
@app.route('/api/students', methods=['GET', 'POST'])
@login_required('teacher')
def api_students():
    if request.method == 'POST':
        data = request.json
        new_id = str(int(time.time()))
        append_sheet_row('students', [new_id, data.get('name'), data.get('class'), data.get('roll'), data.get('phone'), data.get('email'), data.get('parent')])
        return jsonify({'success': True, 'id': new_id})
    return jsonify(get_sheet_records('students'))

@app.route('/api/students/<student_id>', methods=['DELETE'])
@login_required('teacher')
def api_delete_student(student_id):
    success = delete_sheet_row('students', 'id', student_id)
    return jsonify({'success': success})

@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def api_attendance():
    if request.method == 'POST':
        # Teacher saving attendance
        if session.get('user_role') != 'teacher':
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        date = data.get('date')
        records = data.get('records', []) # [{'student_id': '...', 'status': 'Present/Absent'}]
        for record in records:
            append_sheet_row('attendance', [date, record.get('student_id'), record.get('status')])
        return jsonify({'success': True})

    # GET
    date = request.args.get('date')
    all_attendance = get_sheet_records('attendance')
    if date:
        filtered = [a for a in all_attendance if a.get('date') == date]
        return jsonify(filtered)

    # If student, only return their attendance
    if session.get('user_role') == 'student':
        student_id = session.get('student_id')
        filtered = [a for a in all_attendance if str(a.get('student_id')) == str(student_id)]
        return jsonify(filtered)

    return jsonify(all_attendance)

@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        append_sheet_row('videos', [data.get('date'), data.get('subject'), data.get('drive_link')])
        return jsonify({'success': True})
    return jsonify(get_sheet_records('videos'))

@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required()
def api_subjects():
    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        append_sheet_row('subjects', [data.get('subject_name')])
        return jsonify({'success': True})
    return jsonify(get_sheet_records('subjects'))

@app.route('/api/subjects/<subject_name>', methods=['DELETE'])
@login_required('teacher')
def api_delete_subject(subject_name):
    success = delete_sheet_row('subjects', 'subject_name', subject_name)
    return jsonify({'success': success})

@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        date = time.strftime('%Y-%m-%d')
        append_sheet_row('announcements', [date, data.get('message')])
        return jsonify({'success': True})
    return jsonify(get_sheet_records('announcements'))

# --- Dashboard Stats API ---
@app.route('/api/stats', methods=['GET'])
@login_required('teacher')
def api_stats():
    students = get_sheet_records('students')
    attendance = get_sheet_records('attendance')
    today = time.strftime('%Y-%m-%d')
    today_attendance = [a for a in attendance if a.get('date') == today and a.get('status') == 'Present']
    return jsonify({
        'total_students': len(students),
        'today_present': len(today_attendance)
    })

if __name__ == '__main__':
    app.run(debug=True)

# --- AI Endpoints ---
from openai import OpenAI

# Initialize OpenAI client
client = None
try:
    if os.getenv('OPENAI_API_KEY'):
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
except Exception as e:
    print(f"Failed to initialize OpenAI client: {e}")

def call_openai(prompt, system_message="You are a helpful AI assistant for a coaching class."):
    if not client:
        return "AI features are currently unavailable (OpenAI API key missing or invalid)."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "An error occurred while communicating with the AI. Please try again later."


@app.route('/api/ai/doubt', methods=['POST'])
@login_required('student')
def ai_doubt_solver():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({'success': False, 'error': 'No question provided'})

    prompt = f"Explain this concept in very simple words for a school student: {question}. If it's a math question, give a step-by-step solution."
    answer = call_openai(prompt, "You are a friendly and simple AI tutor.")
    return jsonify({'success': True, 'answer': answer})


@app.route('/api/ai/chat', methods=['POST'])
@login_required('student')
def ai_chat():
    data = request.json
    message = data.get('message')
    if not message:
        return jsonify({'success': False, 'error': 'No message provided'})

    prompt = f"Student message: {message}"
    answer = call_openai(prompt, "You are a friendly tutor. Help the student with concept doubts, exam preparation, or study tips.")
    return jsonify({'success': True, 'answer': answer})


@app.route('/api/ai/attendance', methods=['POST'])
@login_required('teacher')
def ai_attendance_analysis():
    # Analyze raw attendance data
    attendance = get_sheet_records('attendance')
    if not attendance:
        return jsonify({'success': False, 'error': 'No attendance data found.'})

    # Structure data for AI
    student_records = {}
    for record in attendance:
        sid = str(record.get('student_id'))
        if sid not in student_records:
            student_records[sid] = {'Present': 0, 'Absent': 0}
        status = record.get('status')
        if status in ['Present', 'Absent']:
            student_records[sid][status] += 1

    prompt = f"Analyze attendance data and provide insights. Raw data: {json.dumps(student_records)}. Format the summary nicely, identify irregular students (high absents), calculate attendance percentages, and suggest actions."
    answer = call_openai(prompt, "You are an AI EdTech analyst.")
    return jsonify({'success': True, 'answer': answer})


@app.route('/api/ai/video-summary', methods=['POST'])
@login_required('teacher')
def ai_video_summary():
    data = request.json
    topic = data.get('topic')
    if not topic:
        return jsonify({'success': False, 'error': 'No topic provided'})

    prompt = f"Generate summary notes for revision for the topic: {topic}. Include key points and brief summary."
    answer = call_openai(prompt, "You are an expert teacher creating study notes.")
    return jsonify({'success': True, 'answer': answer})


@app.route('/api/ai/quiz', methods=['POST'])
@login_required('teacher')
def ai_quiz_generator():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')
    if not subject or not topic:
        return jsonify({'success': False, 'error': 'Subject and topic required'})

    prompt = f"Generate 5 MCQ questions with answers for {subject} on the topic {topic}."
    answer = call_openai(prompt, "You are an examiner. Format clearly with questions and distinct answers.")
    return jsonify({'success': True, 'answer': answer})


@app.route('/api/ai/announcement', methods=['POST'])
@login_required('teacher')
def ai_announcement():
    data = request.json
    context = data.get('context')
    if not context:
        return jsonify({'success': False, 'error': 'No context provided'})

    prompt = f"Write a professional coaching class announcement. Context: {context}"
    answer = call_openai(prompt, "You are a professional administrator for a coaching class.")
    return jsonify({'success': True, 'answer': answer})

