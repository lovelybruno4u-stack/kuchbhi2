import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, abort

import gspread
from google.oauth2.service_account import Credentials

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Google Sheets Database Layer ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = 'CREDENTIALS.JSON'
MOCK_DB_MODE = False
MOCK_DATA = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def init_gspread():
    global MOCK_DB_MODE
    try:
        # Check if credentials exist and are valid JSON
        with open(CREDENTIALS_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                raise ValueError("CREDENTIALS.JSON is empty.")
            json.loads(content) # validate json

        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        # Attempt to open the project database
        # For simplicity in this demo, we assume the sheet is shared with the service account
        # and we look for 'AswathamaClassesDB' or create it if not found.
        # Alternatively, we could expect the Sheet ID to be in .env, but let's use a dynamic search.

        # In a real environment, user needs to create the sheet and share it.
        # Here we'll just return the client, and the helper functions will use it.
        # We need a spreadsheet ID. Let's assume it's set in ENV, or we'll fallback to mock.
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        if not sheet_id:
            logger.warning("GOOGLE_SHEET_ID not set in .env. Falling back to Mock DB.")
            MOCK_DB_MODE = True
            return None

        sheet = client.open_by_key(sheet_id)
        MOCK_DB_MODE = False
        return sheet
    except Exception as e:
        logger.warning(f"Failed to initialize gspread: {e}. Falling back to Mock DB.")
        MOCK_DB_MODE = True
        return None

gc_sheet = init_gspread()

def get_sheet_data(sheet_name):
    """Retrieve all records from a specific sheet."""
    if MOCK_DB_MODE:
        return MOCK_DATA.get(sheet_name, [])
    try:
        worksheet = gc_sheet.worksheet(sheet_name)
        return worksheet.get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        logger.warning(f"Worksheet '{sheet_name}' not found.")
        return []
    except Exception as e:
        logger.error(f"Error reading from sheet '{sheet_name}': {e}")
        return []

def append_sheet_data(sheet_name, row_dict):
    """Append a row to a specific sheet."""
    if MOCK_DB_MODE:
        if sheet_name not in MOCK_DATA:
            MOCK_DATA[sheet_name] = []
        MOCK_DATA[sheet_name].append(row_dict)
        return True
    try:
        worksheet = gc_sheet.worksheet(sheet_name)
        # We need to ensure columns align. Best effort: get headers.
        headers = worksheet.row_values(1)
        if not headers:
            # Initialize headers if empty based on row_dict keys
            headers = list(row_dict.keys())
            worksheet.append_row(headers)

        row_values = [row_dict.get(h, '') for h in headers]
        worksheet.append_row(row_values)
        return True
    except Exception as e:
        logger.error(f"Error appending to sheet '{sheet_name}': {e}")
        return False

# --- Authentication & Role-based Access ---

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                # If API endpoint, return JSON error
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Authentication required.'}), 401
                return redirect(url_for('login'))

            if role and session.get('user_role') != role:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Forbidden access.'}), 403
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- Basic Routes ---

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

        # Authentication logic
        if role == 'teacher':
            # Teacher login: in a real app, verify against a DB. For this demo, check simple credentials.
            # However, memory mentions to provide a secure system. Let's still allow admin/admin as the sole teacher for this implementation scope.
            if username == 'admin' and password == 'admin':
                session['user_role'] = 'teacher'
                session['user_id'] = 'teacher_1'
                session['user_name'] = 'Admin Teacher'
                return redirect(url_for('teacher_dashboard'))

        elif role == 'student':
            students = get_sheet_data('students')
            # Look for a student whose roll number matches the username and phone matches password (as a simple secure mechanism)
            # Or fallback to demo student/student ONLY IF no students exist.
            matched_student = None
            if students:
                for s in students:
                    if str(s.get('roll', '')) == username and str(s.get('phone', '')) == password:
                        matched_student = s
                        break

            if matched_student:
                session['user_role'] = 'student'
                session['user_id'] = str(matched_student.get('id', ''))
                session['user_name'] = matched_student.get('name', 'Student')
                return redirect(url_for('student_dashboard'))
            elif username == 'student' and password == 'student' and not students:
                 session['user_role'] = 'student'
                 session['user_id'] = 'student_demo'
                 session['user_name'] = 'Demo Student'
                 return redirect(url_for('student_dashboard'))

        return render_template('login.html', error='Invalid credentials.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Teacher Pages ---

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

# --- Student Pages ---

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    return render_template('student/student_dashboard.html')

@app.route('/student/videos')
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
def student_announcements_view():
    return render_template('student/announcements_view.html')




# --- Database / API Layer ---

# --- API: Students ---
@app.route('/api/students', methods=['GET', 'POST'])
@login_required(role='teacher')
def api_students():
    if request.method == 'GET':
        students = get_sheet_data('students')
        return jsonify({'success': True, 'data': students})

    if request.method == 'POST':
        data = request.json
        import uuid
        # Generate a unique ID if adding new
        student_id = str(uuid.uuid4())

        row_dict = {
            'id': student_id,
            'name': data.get('name', ''),
            'class': data.get('class', ''),
            'roll': data.get('roll', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'parent': data.get('parent', '')
        }
        success = append_sheet_data('students', row_dict)
        if success:
            return jsonify({'success': True, 'message': 'Student added successfully'})
        return jsonify({'success': False, 'message': 'Failed to add student'}), 500

@app.route('/api/students/<student_id>', methods=['DELETE', 'PUT'])
@login_required(role='teacher')
def api_student_action(student_id):
    # For full functionality in Google Sheets, we need to update/delete specific rows.
    # In Mock DB, we can just filter it out.
    if MOCK_DB_MODE:
        if request.method == 'DELETE':
            MOCK_DATA['students'] = [s for s in MOCK_DATA.get('students', []) if str(s.get('id')) != student_id]
            return jsonify({'success': True})
        elif request.method == 'PUT':
            data = request.json
            for s in MOCK_DATA.get('students', []):
                if str(s.get('id')) == student_id:
                    s.update({
                        'name': data.get('name', s.get('name')),
                        'class': data.get('class', s.get('class')),
                        'roll': data.get('roll', s.get('roll')),
                        'phone': data.get('phone', s.get('phone')),
                        'email': data.get('email', s.get('email')),
                        'parent': data.get('parent', s.get('parent'))
                    })
            return jsonify({'success': True})

    else:
        # Implementing actual sheet update/delete is complex with gspread without row indices.
        # We will fetch all records, find the row (index + 2 because of headers), and delete/update it.
        try:
            worksheet = gc_sheet.worksheet('students')
            records = worksheet.get_all_records()
            row_idx = None
            for idx, r in enumerate(records):
                if str(r.get('id')) == str(student_id):
                    row_idx = idx + 2
                    break

            if not row_idx:
                return jsonify({'success': False, 'message': 'Student not found'}), 404

            if request.method == 'DELETE':
                worksheet.delete_rows(row_idx)
                return jsonify({'success': True})

            if request.method == 'PUT':
                data = request.json
                headers = worksheet.row_values(1)

                # Update cells
                cells_to_update = []
                for col_idx, header in enumerate(headers):
                    val = data.get(header)
                    if val is not None:
                         # 1-indexed for both
                         cells_to_update.append(gspread.Cell(row=row_idx, col=col_idx+1, value=val))
                if cells_to_update:
                    worksheet.update_cells(cells_to_update)

                return jsonify({'success': True})

        except Exception as e:
            logger.error(f"Error managing student {student_id}: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

# --- API: Attendance ---
@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def api_attendance():
    if request.method == 'GET':
        records = get_sheet_data('attendance')
        # Filter for student if student role
        if session.get('user_role') == 'student':
            student_id = session.get('user_id')
            records = [r for r in records if str(r.get('student_id')) == str(student_id)]
        return jsonify({'success': True, 'data': records})

    if request.method == 'POST':
        # Teacher submitting attendance
        if session.get('user_role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403

        data = request.json
        date = data.get('date')
        records = data.get('records', [])

        # Delete existing attendance for this date
        if MOCK_DB_MODE:
            MOCK_DATA['attendance'] = [r for r in MOCK_DATA.get('attendance', []) if r.get('date') != date]
            for r in records:
                append_sheet_data('attendance', {
                    'date': date,
                    'student_id': r.get('student_id'),
                    'status': r.get('status')
                })
            return jsonify({'success': True})
        else:
            try:
                worksheet = gc_sheet.worksheet('attendance')
                all_recs = worksheet.get_all_records()
                # Finding rows to delete backwards to not mess up indices
                rows_to_delete = []
                for i, r in enumerate(all_recs):
                    if r.get('date') == date:
                        rows_to_delete.append(i + 2)

                for row_idx in reversed(rows_to_delete):
                     worksheet.delete_rows(row_idx)

                # Append new records
                rows_to_append = []
                headers = worksheet.row_values(1)
                for r in records:
                     row_dict = {
                         'date': date,
                         'student_id': r.get('student_id'),
                         'status': r.get('status')
                     }
                     rows_to_append.append([row_dict.get(h, '') for h in headers])

                if rows_to_append:
                    worksheet.append_rows(rows_to_append)

                return jsonify({'success': True})
            except Exception as e:
                logger.error(f"Error updating attendance: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500

# --- API: Videos ---
@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'GET':
        records = get_sheet_data('videos')
        return jsonify({'success': True, 'data': records})

    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        row_dict = {
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'subject': data.get('subject', ''),
            'drive_link': data.get('drive_link', '')
        }
        success = append_sheet_data('videos', row_dict)
        return jsonify({'success': success})

# --- API: Subjects ---
@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required()
def api_subjects():
    if request.method == 'GET':
        records = get_sheet_data('subjects')
        return jsonify({'success': True, 'data': records})

    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        row_dict = {
            'subject_name': data.get('subject_name', '')
        }
        success = append_sheet_data('subjects', row_dict)
        return jsonify({'success': success})

@app.route('/api/subjects/<subject_name>', methods=['DELETE', 'PUT'])
@login_required(role='teacher')
def api_delete_subject(subject_name):
    if MOCK_DB_MODE:
        if request.method == 'DELETE':
            MOCK_DATA['subjects'] = [s for s in MOCK_DATA.get('subjects', []) if str(s.get('subject_name')) != subject_name]
            return jsonify({'success': True})
        if request.method == 'PUT':
            data = request.json
            for s in MOCK_DATA.get('subjects', []):
                if str(s.get('subject_name')) == subject_name:
                    s['subject_name'] = data.get('subject_name')
            return jsonify({'success': True})
    else:
        try:
            worksheet = gc_sheet.worksheet('subjects')
            records = worksheet.get_all_records()
            row_idx = None
            for idx, r in enumerate(records):
                if str(r.get('subject_name')) == str(subject_name):
                    row_idx = idx + 2
                    break

            if not row_idx:
                return jsonify({'success': False, 'message': 'Subject not found'}), 404

            if request.method == 'DELETE':
                worksheet.delete_rows(row_idx)
                return jsonify({'success': True})

            if request.method == 'PUT':
                data = request.json
                new_name = data.get('subject_name')
                if new_name:
                    worksheet.update_cell(row_idx, 1, new_name)
                return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error deleting subject {subject_name}: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

# --- API: Announcements ---
@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'GET':
        records = get_sheet_data('announcements')
        # Reverse to show newest first
        records = list(reversed(records))
        return jsonify({'success': True, 'data': records})

    if request.method == 'POST':
        if session.get('user_role') != 'teacher':
             return jsonify({'success': False, 'error': 'Forbidden'}), 403
        data = request.json
        row_dict = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': data.get('message', '')
        }
        success = append_sheet_data('announcements', row_dict)
        return jsonify({'success': success})


# --- AI Features Layer ---
from openai import OpenAI

def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        logger.warning("OPENAI_API_KEY is not set or is default.")
        return None
    return OpenAI(api_key=api_key)

@app.route('/api/ai/doubt', methods=['POST'])
@login_required(role='student')
def ai_doubt_solver():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    data = request.json
    question = data.get('question', '')

    if not question:
         return jsonify({'success': False, 'error': 'No question provided.'}), 400

    system_prompt = "Explain this concept in very simple words for a school student. If it is a math question, give step by step solution."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"OpenAI error (Doubt Solver): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def ai_study_chatbot():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    data = request.json
    message = data.get('message', '')
    history = data.get('history', [])

    if not message:
         return jsonify({'success': False, 'error': 'No message provided.'}), 400

    system_prompt = "You are a friendly AI tutor for a student. Help them with concept doubts, exam preparation, and study tips."

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        answer = response.choices[0].message.content
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f"OpenAI error (Chatbot): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/attendance', methods=['POST'])
@login_required(role='teacher')
def ai_attendance_analysis():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    # Get raw attendance data
    attendance_data = get_sheet_data('attendance')
    students_data = get_sheet_data('students')

    if not attendance_data:
        return jsonify({'success': False, 'error': 'No attendance data found.'}), 400

    # Structure data for AI
    student_map = {str(s.get('id')): s.get('name') for s in students_data}
    structured_data = {}

    for r in attendance_data:
        s_id = str(r.get('student_id'))
        name = student_map.get(s_id, 'Unknown')
        status = r.get('status', '').lower()
        if name not in structured_data:
            structured_data[name] = {'present': 0, 'absent': 0}

        if status == 'present':
            structured_data[name]['present'] += 1
        elif status == 'absent':
            structured_data[name]['absent'] += 1

    prompt_data = json.dumps(structured_data)
    system_prompt = "Analyze attendance data and provide insights. State which students are irregular, their attendance percentage, and suggest actions."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the attendance data: {prompt_data}"}
            ]
        )
        analysis = response.choices[0].message.content
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        logger.error(f"OpenAI error (Attendance): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required(role='teacher')
def ai_video_summary():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    data = request.json
    topic = data.get('topic', '')

    if not topic:
         return jsonify({'success': False, 'error': 'No topic provided.'}), 400

    system_prompt = "Generate summary notes for revision. Include a brief summary and key points based on the topic provided."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Video Topic: {topic}"}
            ]
        )
        summary = response.choices[0].message.content
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        logger.error(f"OpenAI error (Video Summary): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz_generator():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    data = request.json
    subject = data.get('subject', '')
    topic = data.get('topic', '')

    if not topic:
         return jsonify({'success': False, 'error': 'No topic provided.'}), 400

    system_prompt = "Generate 5 MCQ questions with answers based on the subject and topic. Format the output clearly."
    user_prompt = f"Subject: {subject}\nTopic: {topic}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        quiz = response.choices[0].message.content
        return jsonify({'success': True, 'quiz': quiz})
    except Exception as e:
        logger.error(f"OpenAI error (Quiz Generator): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='teacher')
def ai_announcement():
    client = get_openai_client()
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI API key not configured.'}), 500

    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
         return jsonify({'success': False, 'error': 'No prompt provided.'}), 400

    system_prompt = "Write a professional coaching class announcement."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        announcement = response.choices[0].message.content
        return jsonify({'success': True, 'announcement': announcement})
    except Exception as e:
        logger.error(f"OpenAI error (Announcement): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
