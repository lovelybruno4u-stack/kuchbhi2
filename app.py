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
            if init_google_sheet(gc):
                app.config['db_initialized'] = True
                print("Database initialized successfully.")
            else:
                print("Database initialization failed.")
        else:
            print("Could not initialize DB: no Google Credentials provided.")
            app.config['db_initialized'] = False


# Initialize OpenAI Client
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Google Sheets Setup
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')  # JSON string from Render env var
CREDENTIALS_FILE = 'credentials.json'

def get_gspread_client():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
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

def init_google_sheet(gc, admin_email=None):
    """Creates or prepares the Google Sheet with required tabs and headers."""
    global SPREADSHEET_ID

    sheets_schema = {
        'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'],
        'attendance': ['date', 'student_id', 'status'],
        'videos': ['id', 'date', 'subject', 'drive_link'],
        'subjects': ['id', 'subject_name'],
        'announcements': ['id', 'date', 'message']
    }

    sh = None
    if SPREADSHEET_ID:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            print(f"Connected to existing spreadsheet: {SPREADSHEET_ID}")
        except gspread.exceptions.APIError:
            print("Spreadsheet ID provided but could not be accessed. Creating new one.")
            sh = None

    if not sh:
        try:
            print("Creating new Google Spreadsheet: 'Aswathama Classes Database'")
            sh = gc.create('Aswathama Classes Database')
            SPREADSHEET_ID = sh.id
            print(f"Successfully created! New SPREADSHEET_ID: {SPREADSHEET_ID}")
            # If an admin email is provided via environment, share it with them
            share_email = os.getenv('ADMIN_EMAIL') or admin_email
            if share_email:
                try:
                    sh.share(share_email, perm_type='user', role='writer')
                    print(f"Shared spreadsheet with {share_email}")
                except Exception as e:
                    print(f"Could not share sheet: {e}")
            else:
                print("WARNING: No ADMIN_EMAIL provided in env vars. You will not be able to view this sheet in your Google Drive UI because it is owned by the Service Account. Please add ADMIN_EMAIL to .env or Render and restart.")
        except Exception as e:
            print(f"Failed to create new spreadsheet: {e}")
            return False

    # Ensure all required worksheets exist and have headers
    existing_worksheets = [ws.title for ws in sh.worksheets()]

    for sheet_name, headers in sheets_schema.items():
        if sheet_name not in existing_worksheets:
            print(f"Creating missing worksheet: {sheet_name}")
            ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
            ws.append_row(headers)
        else:
            ws = sh.worksheet(sheet_name)
            # Basic check if empty (might not have headers)
            if len(ws.get_all_values()) == 0:
                ws.append_row(headers)

    # Remove default 'Sheet1' if it exists and we've created our custom ones
    if 'Sheet1' in existing_worksheets and 'students' in sheets_schema:
        try:
            sh.del_worksheet(sh.worksheet('Sheet1'))
        except Exception:
            pass

    return True

def get_google_sheet(sheet_name):
    """Helper to get a specific worksheet from Google Sheets."""
    gc = get_gspread_client()
    if not gc:
        return None

    global SPREADSHEET_ID
    if not SPREADSHEET_ID:
        success = init_google_sheet(gc)
        if not success:
            return None

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.worksheet(sheet_name)
    except Exception as e:
        print(f"Error accessing Google Sheets ({sheet_name}): {e}")
        return None


# MOCK DATA FOR DEVELOPMENT WITHOUT ACTIVE GOOGLE SHEET
mock_db = {
    'students': [{'id': '1', 'name': 'John Doe', 'class': '10th', 'roll': '101', 'phone': '1234567890', 'email': 'john@example.com', 'parent': 'Jane Doe'}],
    'attendance': [{'date': '2023-10-01', 'student_id': '1', 'status': 'Present'}],
    'videos': [{'id': '1', 'date': '2023-10-01', 'subject': 'Physics - Motion', 'drive_link': 'https://drive.google.com/mock'}],
    'subjects': [{'id': '1', 'subject_name': 'Physics'}, {'id': '2', 'subject_name': 'Mathematics'}],
    'announcements': [{'id': '1', 'date': '2023-10-01', 'message': 'Welcome to Aswathama Classes!'}]
}

def get_data(sheet_name):
    # Try getting from Google Sheets first, fallback to mock data
    sheet = get_google_sheet(sheet_name)
    if sheet:
        return sheet.get_all_records()
    else:
        print(f"Using mock data for {sheet_name}")
        return mock_db.get(sheet_name, [])

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

        if role == 'teacher' and username == 'admin' and password == 'admin':
            session['user_role'] = 'teacher'
            session['user_name'] = 'Teacher'
            return redirect(url_for('teacher_dashboard'))
        elif role == 'student' and username == 'student' and password == 'student':
            session['user_role'] = 'student'
            session['user_name'] = 'John Doe'
            session['student_id'] = '1'
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

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
    # In a real app, append to Google Sheet
    new_student = {
        'id': str(len(mock_db['students']) + 1),
        'name': request.form.get('name'),
        'class': request.form.get('student_class'),
        'roll': request.form.get('roll'),
        'phone': request.form.get('phone'),
        'email': request.form.get('email'),
        'parent': request.form.get('parent')
    }
    mock_db['students'].append(new_student)
    flash('Student added successfully!', 'success')
    return redirect(url_for('teacher_students'))

@app.route('/teacher/delete_student/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_student(id):
    mock_db['students'] = [s for s in mock_db['students'] if s.get('id') != id]
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

    for record in records:
        mock_db['attendance'].append({
            'date': date,
            'student_id': record['student_id'],
            'status': record['status']
        })
    return jsonify({'success': True})

@app.route('/teacher/videos')
@login_required(role='teacher')
def teacher_videos():
    videos = get_data('videos')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('teacher/videos.html', videos=videos, current_date=current_date)

@app.route('/teacher/add_video', methods=['POST'])
@login_required(role='teacher')
def add_video():
    new_video = {
        'id': str(len(mock_db['videos']) + 1),
        'date': request.form.get('date'),
        'subject': request.form.get('subject'),
        'drive_link': request.form.get('drive_link')
    }
    mock_db['videos'].append(new_video)
    flash('Video added successfully!', 'success')
    return redirect(url_for('teacher_videos'))

@app.route('/teacher/delete_video/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_video(id):
    mock_db['videos'] = [v for v in mock_db['videos'] if v.get('id') != id]
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
    new_sub = {
        'id': str(len(mock_db['subjects']) + 1),
        'subject_name': request.form.get('subject_name')
    }
    mock_db['subjects'].append(new_sub)
    flash('Subject added!', 'success')
    return redirect(url_for('teacher_subjects'))

@app.route('/teacher/delete_subject/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_subject(id):
    mock_db['subjects'] = [s for s in mock_db['subjects'] if s.get('id') != id]
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
    new_ann = {
        'id': str(len(mock_db['announcements']) + 1),
        'date': request.form.get('date'),
        'message': request.form.get('message')
    }
    mock_db['announcements'].append(new_ann)
    flash('Announcement posted!', 'success')
    return redirect(url_for('teacher_announcements'))

@app.route('/teacher/delete_announcement/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_announcement(id):
    mock_db['announcements'] = [a for a in mock_db['announcements'] if a.get('id') != id]
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
@app.route('/student/dashboard')
@login_required(role='student')
def old_student_dashboard():
    return render_template('student/student_dashboard.html')

@app.route('/student/my_videos')
@login_required(role='student')
def old_student_my_videos():
    return render_template('student/my_videos.html')

@app.route('/student/attendance')
@login_required(role='student')
def old_student_attendance_view():
    return render_template('student/attendance_view.html')

@app.route('/student/chatbot')
@login_required(role='student')
def old_student_chatbot():
    return render_template('student/chatbot.html')

@app.route('/student/announcements')
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
    attendance = [a for a in mock_db['attendance'] if a['student_id'] == student_id]
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
    attendance_records = [a for a in mock_db['attendance'] if a['student_id'] == student_id]

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
