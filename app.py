import os
import uuid
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-dev-secret-key')

# OpenAI Setup
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Google Sheets Setup
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "CREDENTIALS.JSON"
# Use a default Sheet ID or environment variable for the real database
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "YOUR_SPREADSHEET_ID_HERE")

gc = None
try:
    if os.path.exists(CREDENTIALS_FILE):
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
        gc = gspread.authorize(credentials)
except Exception as e:
    print(f"Warning: Failed to authenticate with Google Sheets: {e}")

# In-memory mock DB fallback
mock_db = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def get_sheet(sheet_name):
    if gc and SPREADSHEET_ID != "YOUR_SPREADSHEET_ID_HERE":
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            return sh.worksheet(sheet_name)
        except Exception as e:
            print(f"Error accessing sheet {sheet_name}: {e}")
            return None
    return None

def fetch_all(sheet_name):
    sheet = get_sheet(sheet_name)
    if sheet:
        records = sheet.get_all_records()
        return records
    return mock_db.get(sheet_name, [])

def append_row(sheet_name, row_data):
    sheet = get_sheet(sheet_name)
    if sheet:
        sheet.append_row(row_data)
    else:
        if sheet_name == 'students':
            mock_db['students'].append({
                'id': row_data[0], 'name': row_data[1], 'class': row_data[2],
                'roll': row_data[3], 'phone': row_data[4], 'email': row_data[5], 'parent': row_data[6]
            })
        elif sheet_name == 'attendance':
            mock_db['attendance'].append({
                'date': row_data[0], 'student_id': row_data[1], 'status': row_data[2]
            })
        elif sheet_name == 'videos':
            mock_db['videos'].append({
                'date': row_data[0], 'subject': row_data[1], 'drive_link': row_data[2]
            })
        elif sheet_name == 'subjects':
            mock_db['subjects'].append({'subject_name': row_data[0]})
        elif sheet_name == 'announcements':
            mock_db['announcements'].append({'date': row_data[0], 'message': row_data[1]})

def delete_row_by_id(sheet_name, col_name, item_id):
    sheet = get_sheet(sheet_name)
    if sheet:
        records = sheet.get_all_records()
        for idx, row in enumerate(records):
            if str(row.get(col_name)) == str(item_id):
                sheet.delete_rows(idx + 2) # +2 because row 1 is header and idx is 0-based
                break
    else:
        mock_db[sheet_name] = [item for item in mock_db[sheet_name] if str(item.get(col_name)) != str(item_id)]

# Auth Decorator
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

# ---- ROUTES ----

@app.route('/')
def index():
    if 'user_role' in session:
        if session['user_role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif session['user_role'] == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        # Simple mock auth logic for demonstration
        if role == 'teacher' and username == 'admin' and password == 'admin':
            session['user_role'] = 'teacher'
            session['user_id'] = 'teacher_1'
            session['user_name'] = 'Teacher'
            return redirect(url_for('teacher_dashboard'))
        elif role == 'student' and username == 'student' and password == 'student':
            # For a real app, verify against db. Here, if student is 'student', grab first student from db to link if possible
            students = fetch_all('students')
            user_id = students[0]['id'] if students else 'student_1'
            user_name = students[0]['name'] if students else 'Demo Student'

            session['user_role'] = 'student'
            session['user_id'] = user_id
            session['user_name'] = user_name
            return redirect(url_for('student_dashboard'))
        elif role == 'student' and username and password:
            # simple mock match by username/roll/email
            students = fetch_all('students')
            for s in students:
                if str(s.get('roll')) == username or str(s.get('email')) == username or s.get('name') == username:
                    session['user_role'] = 'student'
                    session['user_id'] = str(s.get('id'))
                    session['user_name'] = s.get('name')
                    return redirect(url_for('student_dashboard'))
            return render_template('login.html', error='Invalid credentials')
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---- TEACHER ROUTES ----

@app.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    students = fetch_all('students')
    attendance = fetch_all('attendance')
    today_date = datetime.now().strftime("%Y-%m-%d")
    today_attendance = [a for a in attendance if a.get('date') == today_date]

    return render_template('dashboard.html',
                           total_students=len(students),
                           today_attendance=len(today_attendance))

@app.route('/teacher/students')
@login_required(role='teacher')
def students_page():
    return render_template('students.html')

@app.route('/teacher/attendance')
@login_required(role='teacher')
def attendance_page():
    return render_template('attendance.html')

@app.route('/teacher/videos')
@login_required(role='teacher')
def videos_page():
    return render_template('videos.html')

@app.route('/teacher/subjects')
@login_required(role='teacher')
def subjects_page():
    return render_template('subjects.html')

@app.route('/teacher/announcements')
@login_required(role='teacher')
def announcements_page():
    return render_template('announcements.html')

@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def ai_tools_page():
    return render_template('ai_tools.html')

# ---- STUDENT ROUTES ----

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    return render_template('student_dashboard.html', user_name=session.get('user_name'))

@app.route('/student/my_videos')
@login_required(role='student')
def my_videos_page():
    return render_template('my_videos.html')

@app.route('/student/attendance')
@login_required(role='student')
def student_attendance_page():
    return render_template('attendance_view.html')

@app.route('/student/chatbot')
@login_required(role='student')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/student/announcements')
@login_required(role='student')
def student_announcements_page():
    return render_template('announcements_view.html')


# ---- API ENDPOINTS ----

# Students API
@app.route('/api/students', methods=['GET', 'POST'])
@login_required(role='teacher')
def api_students():
    if request.method == 'GET':
        students = fetch_all('students')
        return jsonify(students)

    if request.method == 'POST':
        data = request.json
        student_id = str(uuid.uuid4())[:8]
        row = [
            student_id, data.get('name'), data.get('class'), data.get('roll'),
            data.get('phone'), data.get('email'), data.get('parent')
        ]
        append_row('students', row)
        return jsonify({'success': True, 'message': 'Student added successfully'})

@app.route('/api/students/<student_id>', methods=['PUT'])
@login_required(role='teacher')
def api_edit_student(student_id):
    data = request.json
    # Find and edit the student in the database.
    # We update both mock_db and gspread if connected.

    if gc and SPREADSHEET_ID != "YOUR_SPREADSHEET_ID_HERE":
        sheet = get_sheet('students')
        if sheet:
            records = sheet.get_all_records()
            for idx, row in enumerate(records):
                if str(row.get('id')) == str(student_id):
                    # update row
                    cell_range = f"A{idx+2}:G{idx+2}"
                    sheet.update(cell_range, [[
                        student_id, data.get('name'), data.get('class'), data.get('roll'),
                        data.get('phone'), data.get('email'), data.get('parent')
                    ]])
                    break
    else:
        for i, s in enumerate(mock_db['students']):
            if str(s['id']) == str(student_id):
                mock_db['students'][i].update({
                    'name': data.get('name'), 'class': data.get('class'),
                    'roll': data.get('roll'), 'phone': data.get('phone'),
                    'email': data.get('email'), 'parent': data.get('parent')
                })
                break

    return jsonify({'success': True, 'message': 'Student updated successfully'})


@app.route('/api/students/<student_id>', methods=['DELETE'])
@login_required(role='teacher')
def api_delete_student(student_id):
    delete_row_by_id('students', 'id', student_id)
    return jsonify({'success': True, 'message': 'Student deleted'})

# Attendance API
@app.route('/api/attendance', methods=['GET', 'POST'])
@login_required()
def api_attendance():
    if request.method == 'GET':
        date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        attendance = fetch_all('attendance')
        date_attendance = [a for a in attendance if a.get('date') == date]

        if session.get('user_role') == 'student':
            student_id = session.get('user_id')
            date_attendance = [a for a in attendance if str(a.get('student_id')) == str(student_id)]

        return jsonify(date_attendance)

    if request.method == 'POST' and session.get('user_role') == 'teacher':
        data = request.json
        date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        records = data.get('records', []) # list of {student_id, status}

        # In a real app, you might want to update existing records instead of appending blindly.
        # Here we just append.
        for record in records:
            row = [date, record.get('student_id'), record.get('status')]
            append_row('attendance', row)

        return jsonify({'success': True, 'message': 'Attendance saved'})

# Videos API
@app.route('/api/videos', methods=['GET', 'POST'])
@login_required()
def api_videos():
    if request.method == 'GET':
        videos = fetch_all('videos')
        return jsonify(videos)

    if request.method == 'POST' and session.get('user_role') == 'teacher':
        data = request.json
        row = [data.get('date'), data.get('subject'), data.get('drive_link')]
        append_row('videos', row)
        return jsonify({'success': True, 'message': 'Video added'})

# Subjects API
@app.route('/api/subjects', methods=['GET', 'POST'])
@login_required()
def api_subjects():
    if request.method == 'GET':
        subjects = fetch_all('subjects')
        return jsonify(subjects)

    if request.method == 'POST' and session.get('user_role') == 'teacher':
        data = request.json
        row = [data.get('subject_name')]
        append_row('subjects', row)
        return jsonify({'success': True, 'message': 'Subject added'})

@app.route('/api/subjects/<old_subject_name>', methods=['PUT'])
@login_required(role='teacher')
def api_edit_subject(old_subject_name):
    data = request.json
    new_name = data.get('subject_name')

    if gc and SPREADSHEET_ID != "YOUR_SPREADSHEET_ID_HERE":
        sheet = get_sheet('subjects')
        if sheet:
            records = sheet.get_all_records()
            for idx, row in enumerate(records):
                if str(row.get('subject_name')) == str(old_subject_name):
                    sheet.update_cell(idx+2, 1, new_name)
                    break
    else:
        for i, s in enumerate(mock_db['subjects']):
            if s['subject_name'] == old_subject_name:
                mock_db['subjects'][i]['subject_name'] = new_name
                break

    return jsonify({'success': True, 'message': 'Subject updated'})

@app.route('/api/subjects/<subject_name>', methods=['DELETE'])
@login_required(role='teacher')
def api_delete_subject(subject_name):
    delete_row_by_id('subjects', 'subject_name', subject_name)
    return jsonify({'success': True, 'message': 'Subject deleted'})

# Announcements API
@app.route('/api/announcements', methods=['GET', 'POST'])
@login_required()
def api_announcements():
    if request.method == 'GET':
        announcements = fetch_all('announcements')
        # Sort by date descending in UI
        return jsonify(announcements)

    if request.method == 'POST' and session.get('user_role') == 'teacher':
        data = request.json
        row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('message')]
        append_row('announcements', row)
        return jsonify({'success': True, 'message': 'Announcement added'})


# ---- AI ENDPOINTS ----

@app.route('/api/ai/doubt', methods=['POST'])
@login_required(role='student')
def ai_doubt_solver():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    data = request.json
    question = data.get('question', '')

    prompt = "Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({'answer': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def ai_study_chatbot():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    data = request.json
    message = data.get('message', '')
    history = data.get('history', [])

    messages = [{"role": "system", "content": "You are a friendly and helpful tutor for a school student. Help them with concept doubts, exam preparation, and study tips."}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return jsonify({'reply': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/attendance', methods=['GET'])
@login_required(role='teacher')
def ai_attendance_analysis():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    attendance_data = fetch_all('attendance')
    students_data = fetch_all('students')

    # Structure data for AI
    structured_data = {}
    for s in students_data:
        structured_data[s['id']] = {'name': s['name'], 'present': 0, 'absent': 0}

    for a in attendance_data:
        sid = str(a.get('student_id'))
        if sid in structured_data:
            if a.get('status', '').lower() == 'present':
                structured_data[sid]['present'] += 1
            else:
                structured_data[sid]['absent'] += 1

    prompt = "Analyze attendance data and provide insights. Point out irregular students, overall attendance percentage trends, and suggest actions."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(structured_data)}
            ]
        )
        return jsonify({'analysis': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required(role='teacher')
def ai_video_summary():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    data = request.json
    topic = data.get('topic', '')

    prompt = "Generate summary notes for revision based on the topic. Include a brief summary and key points."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Topic: {topic}"}
            ]
        )
        return jsonify({'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz_generator():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    data = request.json
    subject = data.get('subject', '')
    topic = data.get('topic', '')

    prompt = "Generate 5 MCQ questions with answers. Format clearly."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Subject: {subject}, Topic: {topic}"}
            ]
        )
        return jsonify({'quiz': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='teacher')
def ai_announcement_generator():
    if not openai_client:
        return jsonify({'error': 'OpenAI API key not configured'}), 500

    data = request.json
    topic = data.get('topic', '')

    prompt = "Write a professional coaching class announcement."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )
        return jsonify({'announcement': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
