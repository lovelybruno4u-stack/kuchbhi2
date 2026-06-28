import os
import json
import uuid
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import openai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')
app.permanent_session_lifetime = timedelta(days=365)

# OpenAI Client
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Google Sheets Setup
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1h_vz2JXdDX4GDqkQQwr3mQArHMqsYdem7Xjv8KVkrY8')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
CREDENTIALS_FILE = 'CREDENTIALS.JSON'

def get_gspread_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    try:
        if GOOGLE_CREDENTIALS:
            creds_info = json.loads(GOOGLE_CREDENTIALS)
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        else:
            if not os.path.exists(CREDENTIALS_FILE) or os.path.getsize(CREDENTIALS_FILE) == 0:
                print("Using mock database mode (no valid CREDENTIALS.JSON).")
                return None
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error authenticating with Google: {e}")
        return None

# Simple In-Memory Mock DB
MOCK_DB = {
    'students': [],
    'attendance': [],
    'videos': [],
    'subjects': [],
    'announcements': []
}

def get_google_sheet(sheet_name):
    gc = get_gspread_client()
    if not gc:
        return None
    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        print(f"Cannot access spreadsheet {SPREADSHEET_ID}: {e}")
        return None

    sheets_schema = {
        'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'],
        'attendance': ['date', 'student_id', 'status'],
        'videos': ['date', 'subject', 'drive_link'],
        'subjects': ['subject_name'],
        'announcements': ['date', 'message']
    }

    try:
        ws = sh.worksheet(sheet_name)
    except:
        if sheet_name in sheets_schema:
            try:
                ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
                ws.append_row(sheets_schema[sheet_name])
            except Exception as e:
                print(f"Failed to create worksheet '{sheet_name}': {e}")
                return None
        else:
            return None

    try:
        if len(ws.get_all_values()) == 0 and sheet_name in sheets_schema:
            ws.append_row(sheets_schema[sheet_name])
    except:
        pass
    return ws

def get_data(sheet_name):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        try:
            return sheet.get_all_records()
        except:
            return []
    else:
        return MOCK_DB.get(sheet_name, [])

def add_data_to_sheet(sheet_name, row_dict):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        headers = sheet.row_values(1)
        row_to_insert = [str(row_dict.get(h, '')) for h in headers]
        sheet.append_row(row_to_insert)
        return True
    else:
        MOCK_DB[sheet_name].append(row_dict)
        return True

def delete_data_from_sheet(sheet_name, key_field, key_value):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        records = sheet.get_all_records()
        for index, record in enumerate(records):
            if str(record.get(key_field, '')) == str(key_value):
                sheet.delete_rows(index + 2)
                return True
    else:
        MOCK_DB[sheet_name] = [r for r in MOCK_DB.get(sheet_name, []) if str(r.get(key_field, '')) != str(key_value)]
        return True
    return False

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized'}), 401
                return redirect(url_for('login'))
            if role and session['user_role'] != role:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Forbidden'}), 403
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

        if role == 'teacher':
            if username == 'admin' and password == 'admin':
                session.permanent = True
                session['user_role'] = 'teacher'
                session['user_name'] = 'Admin'
                return redirect(url_for('teacher_dashboard'))
            else:
                flash('Invalid teacher credentials.', 'error')

        elif role == 'student':
            students = get_data('students')
            student_found = None

            # Allow fallback mode using student/student if DB is empty for demo purposes
            if username == 'student' and password == 'student':
                if students:
                    student_found = students[0]
                else:
                    student_found = {'id': 'stu_' + str(uuid.uuid4())[:8], 'name': 'Demo Student', 'roll': 'student'}
                    MOCK_DB['students'].append(student_found)
            else:
                for student in students:
                    if str(student.get('roll')) == str(username) and str(student.get('phone')) == str(password):
                        student_found = student
                        break

            if student_found:
                session.permanent = True
                session['user_role'] = 'student'
                session['user_name'] = student_found.get('name')
                session['student_id'] = student_found.get('id')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid student credentials.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Teacher Routes ---
@app.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    students = get_data('students')
    attendance = get_data('attendance')
    current_date = datetime.now().strftime('%Y-%m-%d')
    today_attendance = len([a for a in attendance if a.get('date') == current_date and a.get('status') == 'Present'])

    stats = {
        'total_students': len(students),
        'today_attendance': today_attendance
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/teacher/students', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_students():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_student = {
                'id': str(uuid.uuid4())[:8],
                'name': request.form.get('name'),
                'class': request.form.get('student_class'),
                'roll': request.form.get('roll'),
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'parent': request.form.get('parent')
            }
            add_data_to_sheet('students', new_student)
            flash('Student added successfully!', 'success')
        elif action == 'edit':
            student_id = request.form.get('id')
            # For simplicity, delete and add back
            delete_data_from_sheet('students', 'id', student_id)
            edited_student = {
                'id': student_id,
                'name': request.form.get('name'),
                'class': request.form.get('student_class'),
                'roll': request.form.get('roll'),
                'phone': request.form.get('phone'),
                'email': request.form.get('email'),
                'parent': request.form.get('parent')
            }
            add_data_to_sheet('students', edited_student)
            flash('Student updated successfully!', 'success')
        elif action == 'delete':
            student_id = request.form.get('id')
            delete_data_from_sheet('students', 'id', student_id)
            flash('Student deleted!', 'success')
        return redirect(url_for('teacher_students'))

    students = get_data('students')
    search_query = request.args.get('search', '').lower()
    if search_query:
        students = [s for s in students if search_query in str(s.get('name', '')).lower() or search_query in str(s.get('roll', '')).lower()]

    return render_template('students.html', students=students, search_query=search_query)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_attendance():
    if request.method == 'POST':
        date = request.form.get('date')
        student_ids = request.form.getlist('student_id')
        statuses = request.form.getlist('status')

        # In a real app we'd batch update, but for this simpler version:
        for sid, status in zip(student_ids, statuses):
            add_data_to_sheet('attendance', {'date': date, 'student_id': sid, 'status': status})
        flash('Attendance saved!', 'success')
        return redirect(url_for('teacher_attendance'))

    students = get_data('students')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('attendance.html', students=students, current_date=current_date)

@app.route('/teacher/videos', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_videos():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_video = {
                'date': request.form.get('date'),
                'subject': request.form.get('subject'),
                'drive_link': request.form.get('drive_link')
            }
            add_data_to_sheet('videos', new_video)
            flash('Video added!', 'success')
        elif action == 'delete':
            drive_link = request.form.get('drive_link')
            delete_data_from_sheet('videos', 'drive_link', drive_link)
            flash('Video deleted!', 'success')
        return redirect(url_for('teacher_videos'))

    videos = get_data('videos')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('videos.html', videos=videos, current_date=current_date)

@app.route('/teacher/subjects', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_subjects():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_sub = {'subject_name': request.form.get('subject_name')}
            add_data_to_sheet('subjects', new_sub)
            flash('Subject added!', 'success')
        elif action == 'edit':
            old_name = request.form.get('old_subject_name')
            new_name = request.form.get('subject_name')
            delete_data_from_sheet('subjects', 'subject_name', old_name)
            add_data_to_sheet('subjects', {'subject_name': new_name})
            flash('Subject updated!', 'success')
        elif action == 'delete':
            sub_name = request.form.get('subject_name')
            delete_data_from_sheet('subjects', 'subject_name', sub_name)
            flash('Subject deleted!', 'success')
        return redirect(url_for('teacher_subjects'))

    subjects = get_data('subjects')
    search_query = request.args.get('search', '').lower()
    if search_query:
        subjects = [s for s in subjects if search_query in str(s.get('subject_name', '')).lower()]
    return render_template('subjects.html', subjects=subjects, search_query=search_query)

@app.route('/teacher/announcements', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_announcements():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            new_ann = {
                'date': request.form.get('date'),
                'message': request.form.get('message')
            }
            add_data_to_sheet('announcements', new_ann)
            flash('Announcement posted!', 'success')
        elif action == 'delete':
            message = request.form.get('message')
            delete_data_from_sheet('announcements', 'message', message)
            flash('Announcement deleted!', 'success')
        return redirect(url_for('teacher_announcements'))

    announcements = get_data('announcements')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('announcements.html', announcements=announcements[::-1], current_date=current_date)

@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def teacher_ai_tools():
    return render_template('ai_tools.html')

# --- Student Routes ---
@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    students = get_data('students')
    student_class = next((s.get('class') for s in students if str(s.get('id')) == str(student_id)), '')

    attendance_data = get_data('attendance')
    student_attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]
    present = len([a for a in student_attendance if a.get('status') == 'Present'])
    total = len(student_attendance) if student_attendance else 1
    attendance_percentage = round((present / total) * 100) if student_attendance else 0

    videos = get_data('videos')
    announcements = get_data('announcements')

    data = {
        'attendance_percentage': attendance_percentage,
        'latest_announcement': announcements[-1] if announcements else None,
        'today_video': videos[-1] if videos else None
    }
    return render_template('student_dashboard.html', data=data)

@app.route('/student/my_videos')
@login_required(role='student')
def student_my_videos():
    videos = get_data('videos')
    return render_template('my_videos.html', videos=videos)

@app.route('/student/attendance')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')
    attendance_data = get_data('attendance')
    records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]

    present = len([a for a in records if a.get('status') == 'Present'])
    absent = len([a for a in records if a.get('status') == 'Absent'])
    total = len(records)
    percentage = round((present / total) * 100) if total > 0 else 0

    return render_template('attendance_view.html', records=records[::-1], present_count=present, absent_count=absent, total_classes=total, attendance_percentage=percentage)

@app.route('/student/announcements')
@login_required(role='student')
def student_announcements_view():
    announcements = get_data('announcements')
    return render_template('announcements_view.html', announcements=announcements[::-1])

@app.route('/student/chatbot')
@login_required(role='student')
def student_chatbot():
    return render_template('chatbot.html')

# --- AI Endpoints ---
@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def ai_chat():
    data = request.json
    messages = data.get('messages', [])
    prompt_type = data.get('type', 'chatbot')

    system_msg = "You are a friendly tutor. Help the student with concept doubts, exam preparation, or study tips."
    if prompt_type == 'doubt_solver':
        system_msg = "Explain this concept in very simple words for a school student. If it is a math question, give a step by step solution."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_msg}] + messages
        )
        return jsonify({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/attendance', methods=['POST'])
@login_required(role='teacher')
def ai_attendance():
    attendance_data = get_data('attendance')
    students = get_data('students')

    # Structure data for AI
    student_stats = {}
    for a in attendance_data:
        sid = str(a.get('student_id'))
        if sid not in student_stats:
            name = next((s.get('name') for s in students if str(s.get('id')) == sid), 'Unknown')
            student_stats[sid] = {'name': name, 'present': 0, 'total': 0}
        student_stats[sid]['total'] += 1
        if a.get('status') == 'Present':
            student_stats[sid]['present'] += 1

    try:
        prompt = f"Analyze attendance data and provide insights. Data: {json.dumps(student_stats)}"
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz():
    data = request.json
    subject = data.get('subject')
    topic = data.get('topic')

    try:
        prompt = f"Generate 5 MCQ questions with answers about {subject}: {topic}."
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required(role='teacher')
def ai_video_summary():
    topic = request.json.get('topic')
    try:
        prompt = f"Generate summary notes for revision for the topic: {topic}"
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='teacher')
def ai_announcement():
    topic = request.json.get('topic')
    try:
        prompt = f"Write a professional coaching class announcement about: {topic}"
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

