import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')

@app.before_request
def setup_db():
    global SPREADSHEET_ID
    if 'db_initialized' not in app.config:
        gc = get_gspread_client()
        if gc:
            try:
                init_google_sheet(gc)
                app.config['db_initialized'] = True
                print("Database initialized successfully.")
            except Exception as e:
                print(f"Database initialization failed during auto-setup: {e}")
                app.config['db_initialized'] = False
        else:
            print("Could not initialize DB: no Google Credentials provided.")
            app.config['db_initialized'] = False


# Initialize OpenAI Client
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Google Sheets Setup
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1h_vz2JXdDX4GDqkQQwr3mQArHMqsYdem7Xjv8KVkrY8')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')  # JSON string from Render env var
CREDENTIALS_FILE = 'credentials.json'

def get_gspread_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    try:
        if GOOGLE_CREDENTIALS:
            creds_info = json.loads(GOOGLE_CREDENTIALS)
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        else:
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error authenticating with Google: {e}")
        return None

def get_google_sheet(sheet_name):
    """Helper to get a specific worksheet from Google Sheets.
       Automatically creates the worksheet with headers if it doesn't exist.
    """
    gc = get_gspread_client()
    if not gc:
        print("Cannot get gspread client. Check JSON credentials.")
        return None

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        print(f"CRITICAL: Cannot access spreadsheet {SPREADSHEET_ID}. Make sure the Service Account email is an EDITOR on the Google Sheet. Error: {e}")
        return None

    try:
        ws = sh.worksheet(sheet_name)
    except Exception as e:
        # Worksheet does not exist, so create it!
        print(f"Worksheet '{sheet_name}' not found. Creating it now...")

        sheets_schema = {
            'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent', 'password'],
            'attendance': ['date', 'student_id', 'status'],
            'videos': ['id', 'date', 'subject', 'drive_link'],
            'subjects': ['id', 'subject_name'],
            'announcements': ['id', 'date', 'message']
        }

        if sheet_name in sheets_schema:
            try:
                ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
                ws.append_row(sheets_schema[sheet_name])
                print(f"Created '{sheet_name}' and populated headers.")
            except Exception as creation_error:
                print(f"Failed to create worksheet '{sheet_name}': {creation_error}")
                return None
        else:
            print(f"Unknown sheet schema requested: {sheet_name}")
            return None

    # Check if empty (missing headers even if it existed)
    try:
        if len(ws.get_all_values()) == 0:
            sheets_schema = {
                'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent', 'password'],
                'attendance': ['date', 'student_id', 'status'],
                'videos': ['id', 'date', 'subject', 'drive_link'],
                'subjects': ['id', 'subject_name'],
                'announcements': ['id', 'date', 'message']
            }
            if sheet_name in sheets_schema:
                ws.append_row(sheets_schema[sheet_name])
                print(f"Populated missing headers on '{sheet_name}'")
    except Exception as e:
        pass

    return ws

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.worksheet(sheet_name)
    except Exception as e:
        print(f"Error accessing Google Sheets ({sheet_name}): {e}")
        return None



def add_data_to_sheet(sheet_name, row_dict):
    try:
        sheet = get_google_sheet(sheet_name)
        if sheet:
            # We must map the dictionary to a list of values based on the sheet headers
            headers = sheet.row_values(1)
            row_to_insert = [str(row_dict.get(h, '')) for h in headers]
            sheet.append_row(row_to_insert)
            return True
    except Exception as e:
        print(f"Failed to add data to {sheet_name} sheet: {e}")
    return False

def delete_data_from_sheet(sheet_name, row_id):
    try:
        sheet = get_google_sheet(sheet_name)
        if sheet:
            records = sheet.get_all_records()
            for index, record in enumerate(records):
                if str(record.get('id', '')) == str(row_id):
                    # +2 because gspread is 1-indexed, and row 1 is headers
                    sheet.delete_rows(index + 2)
                    return True
    except Exception as e:
        print(f"Failed to delete data from {sheet_name} sheet: {e}")
    return False

def get_data(sheet_name):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        try:
            return sheet.get_all_records()
        except Exception as e:
            print(f"Error reading records from {sheet_name}: {e}")
            return []
    else:
        print(f"Failed to access Google Sheet '{sheet_name}'. Ensure tab exists and permissions are granted.")
        return []

# --- Decorators for Authentication ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return redirect(url_for('login'))
            if role and session['user_role'] != role:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Common Routes ---





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
            # Hardcoded single admin teacher as requested
            if username == 'admin' and password == 'admin':
                session['user_role'] = 'teacher'
                session['user_name'] = 'Teacher'
                return redirect(url_for('teacher_dashboard'))
            else:
                flash('Invalid teacher credentials. Please try again.', 'error')

        elif role == 'student':
            # Fetch students from Google Sheets / DB
            students = get_data('students')

            # Find student by roll number (username field) and match password
            student_found = None
            for student in students:
                if str(student.get('roll')) == str(username) and str(student.get('password')) == str(password):
                    student_found = student
                    break

            if student_found:
                session['user_role'] = 'student'
                session['user_name'] = student_found.get('name')
                session['student_id'] = student_found.get('id')
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid student credentials. Please check your Roll Number and Password.', 'error')

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
    videos = get_data('videos')
    announcements = get_data('announcements')

    stats = {
        'total_students': len(students),
        'today_attendance': 95, # Mock percentage
        'total_videos': len(videos),
        'total_announcements': len(announcements)
    }
    return render_template('teacher/dashboard.html', stats=stats)

@app.route('/teacher/students')
@login_required(role='teacher')
def teacher_students():
    students = get_data('students')
    return render_template('teacher/students.html', students=students)

@app.route('/teacher/add_student', methods=['POST'])
@login_required(role='teacher')
def add_student():
    import uuid
    new_student = {
        'id': str(uuid.uuid4())[:8],
        'name': request.form.get('name'),
        'class': request.form.get('student_class'),
        'roll': request.form.get('roll'),
        'phone': request.form.get('phone'),
        'email': request.form.get('email'),
        'parent': request.form.get('parent'),
        'password': request.form.get('password')
    }
    add_data_to_sheet('students', new_student)
    flash('Student added successfully!', 'success')
    return redirect(url_for('teacher_students'))

@app.route('/teacher/delete_student/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_student(id):
    delete_data_from_sheet('students', id)
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('teacher_students'))

@app.route('/teacher/attendance')
@login_required(role='teacher')
def teacher_attendance():
    students = get_data('students')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('teacher/attendance.html', students=students, current_date=current_date)

@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('attendance')
    if sheet:
        rows_to_insert = []
        for record in records:
            # Update local mock db for immediate testing context
            new_record = {
                'date': date,
                'student_id': record['student_id'],
                'status': record['status']
            }
            # Add to bulk insert list
            rows_to_insert.append([date, record['student_id'], record['status']])

        try:
            if rows_to_insert:
                sheet.append_rows(rows_to_insert)
            return jsonify({'success': True})
        except Exception as e:
            print(f"Failed to save attendance bulk: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'Cannot save: Sheet not found'})

@app.route('/teacher/videos')
@login_required(role='teacher')
def teacher_videos():
    videos = get_data('videos')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('teacher/videos.html', videos=videos, current_date=current_date)

@app.route('/teacher/add_video', methods=['POST'])
@login_required(role='teacher')
def add_video():
    import uuid
    new_video = {
        'id': str(uuid.uuid4())[:8],
        'date': request.form.get('date'),
        'subject': request.form.get('subject'),
        'drive_link': request.form.get('drive_link')
    }
    add_data_to_sheet('videos', new_video)
    flash('Video added successfully!', 'success')
    return redirect(url_for('teacher_videos'))

@app.route('/teacher/delete_video/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_video(id):
    delete_data_from_sheet('videos', id)
    flash('Video deleted!', 'success')
    return redirect(url_for('teacher_videos'))

@app.route('/teacher/subjects')
@login_required(role='teacher')
def teacher_subjects():
    subjects = get_data('subjects')
    return render_template('teacher/subjects.html', subjects=subjects)

@app.route('/teacher/add_subject', methods=['POST'])
@login_required(role='teacher')
def add_subject():
    import uuid
    new_sub = {
        'id': str(uuid.uuid4())[:8],
        'subject_name': request.form.get('subject_name')
    }
    add_data_to_sheet('subjects', new_sub)
    flash('Subject added!', 'success')
    return redirect(url_for('teacher_subjects'))

@app.route('/teacher/delete_subject/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_subject(id):
    delete_data_from_sheet('subjects', id)
    flash('Subject deleted!', 'success')
    return redirect(url_for('teacher_subjects'))

@app.route('/teacher/announcements')
@login_required(role='teacher')
def teacher_announcements():
    announcements = get_data('announcements')
    current_date = datetime.now().strftime('%Y-%m-%d')
    # Reverse to show newest first
    return render_template('teacher/announcements.html', announcements=announcements[::-1], current_date=current_date)

@app.route('/teacher/add_announcement', methods=['POST'])
@login_required(role='teacher')
def add_announcement():
    import uuid
    new_ann = {
        'id': str(uuid.uuid4())[:8],
        'date': request.form.get('date'),
        'message': request.form.get('message')
    }
    add_data_to_sheet('announcements', new_ann)
    flash('Announcement posted!', 'success')
    return redirect(url_for('teacher_announcements'))

@app.route('/teacher/delete_announcement/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_announcement(id):
    delete_data_from_sheet('announcements', id)
    flash('Announcement removed!', 'success')
    return redirect(url_for('teacher_announcements'))

@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def teacher_ai_tools():
    return render_template('teacher/ai_tools.html')

# --- API Endpoints for AI Features (Teacher) ---
def ask_openai(system_prompt, user_prompt):
    if not client:
        return "OpenAI API is not configured. Please add OPENAI_API_KEY in .env file."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

@app.route('/api/teacher/generate_announcement', methods=['POST'])
@login_required(role='teacher')
def ai_generate_announcement():
    data = request.json
    topic = data.get('prompt')
    prompt = f"Write a professional coaching class announcement about: {topic}. Keep it concise, respectful, and clear."
    result = ask_openai("You are an administrative assistant for an educational coaching center.", prompt)
    return jsonify({'result': result})

@app.route('/api/teacher/ai_quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz():
    data = request.json
    topic = data.get('topic')
    prompt = f"Generate 5 MCQ questions with answers on the topic: {topic}. Format nicely."
    result = ask_openai("You are an expert teacher creating quizzes.", prompt)
    return jsonify({'result': result})

@app.route('/api/teacher/ai_attendance_analysis', methods=['POST'])
@login_required(role='teacher')
def ai_attendance_analysis():
    # In a real app, serialize attendance data and send to AI
    prompt = "Analyze this attendance data (mock): 95% present overall. John is absent for 3 days. Provide insights and suggest action."
    result = ask_openai("You are an educational data analyst.", prompt)
    return jsonify({'result': result})

@app.route('/api/teacher/ai_video_summary', methods=['POST'])
@login_required(role='teacher')
def ai_video_summary():
    data = request.json
    topic = data.get('topic')
    prompt = f"Generate summary notes and key points for revision on the lecture topic: {topic}"
    result = ask_openai("You are an expert tutor creating revision notes.", prompt)
    return jsonify({'result': result})


# --- Student Routes (Stubs for now) ---
@app.route('/old_student_dashboard')
@login_required(role='student')
def old_student_dashboard():
    return render_template('student/student_dashboard.html')

@app.route('/old_student_my_videos')
@login_required(role='student')
def old_student_my_videos():
    return render_template('student/my_videos.html')

@app.route('/old_student_attendance')
@login_required(role='student')
def old_student_attendance_view():
    return render_template('student/attendance_view.html')

@app.route('/old_student_chatbot')
@login_required(role='student')
def old_student_chatbot():
    return render_template('student/chatbot.html')

@app.route('/old_student_announcements')
@login_required(role='student')
def old_student_announcements_view():
    return render_template('student/announcements_view.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# --- Student Specific Backend Routes ---
@app.route('/student/dashboard', endpoint='student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')

    # Calculate mock attendance stats for this student
    total = len(attendance) if attendance else 1
    present = len([a for a in attendance if a['status'] == 'Present'])
    rate = (present / total) * 100 if total > 0 else 0

    stats = {
        'attendance_rate': round(rate),
        'new_videos': len(videos[-2:]), # Mock new videos
        'new_announcements': len(announcements[-2:])
    }

    recent_announcements = announcements[::-1]

    return render_template('student/student_dashboard.html', stats=stats, recent_announcements=recent_announcements)

@app.route('/student/my_videos', endpoint='student_my_videos')
@login_required(role='student')
def student_my_videos():
    videos = get_data('videos')
    return render_template('student/my_videos.html', videos=videos)

@app.route('/student/attendance', endpoint='student_attendance_view')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')

    total = len(attendance_records)
    present = len([a for a in attendance_records if a['status'] == 'Present'])
    absent = total - present
    percentage = (present / total) * 100 if total > 0 else 0

    return render_template('student/attendance_view.html',
                           attendance_records=attendance_records[::-1],
                           total_classes=total,
                           present_count=present,
                           absent_count=absent,
                           attendance_percentage=percentage)

@app.route('/student/announcements', endpoint='student_announcements_view')
@login_required(role='student')
def student_announcements_view():
    announcements = get_data('announcements')
    return render_template('student/announcements_view.html', announcements=announcements[::-1])

@app.route('/student/chatbot', endpoint='student_chatbot')
@login_required(role='student')
def student_chatbot():
    return render_template('student/chatbot.html')

# --- API Endpoints for AI Features (Student) ---
@app.route('/api/student/doubt_solver', methods=['POST'])
@login_required(role='student')
def api_doubt_solver():
    data = request.json
    question = data.get('question')
    prompt = f"Explain this concept in very simple words for a school student. If it's a math question, give a step-by-step solution. Question: {question}"
    answer = ask_openai("You are a friendly, encouraging AI tutor for school students.", prompt)
    return jsonify({'answer': answer})

@app.route('/api/chatbot', methods=['POST'])
@login_required(role='student')
def api_chatbot():
    data = request.json
    message = data.get('message')
    prompt = f"Student says: {message}. Give a helpful, encouraging, and brief response."
    reply = ask_openai("You are a friendly, knowledgeable AI study buddy. You help students prepare for exams, learn concepts, and stay motivated.", prompt)
    return jsonify({'reply': reply})
