import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, render_template_string
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Load environment variables
load_dotenv()


from datetime import timedelta
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')
app.permanent_session_lifetime = timedelta(days=365)

# ==========================================
# GLOBAL HARDENED ERROR HANDLING
# ==========================================
import traceback
from werkzeug.exceptions import HTTPException


# ==========================================
# ENTERPRISE SECURITY HEADERS
# ==========================================
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Optional: response.headers['Content-Security-Policy'] = "default-src 'self' https: 'unsafe-inline' 'unsafe-eval'"
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors (like 404s, 401s)
    if isinstance(e, HTTPException):
        # We can handle them gracefully or pass them through
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': e.description}), e.code
        return f"<h1>Error {e.code}</h1><p>{e.description}</p>", e.code

    # Handle completely unhandled Server Errors (500)
    print("FATAL UNHANDLED EXCEPTION:", traceback.format_exc())

    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'The server encountered an internal error. Please try again later.'
        }), 500

    # For UI routes, show a nice premium fallback rather than a crash log
    return render_template_string('''
        <html>
            <head>
                <title>System Error | Ashwathama Classes</title>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
                <style>
                    body { font-family: 'Poppins', sans-serif; background: #f8fafc; color: #1e293b; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.05); text-align: center; max-width: 500px; }
                    h1 { color: #dc2626; margin-bottom: 10px; font-weight: 800; font-size: 2.5rem; }
                    p { color: #64748b; margin-bottom: 30px; line-height: 1.6; }
                    a { display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 12px; font-weight: 600; transition: all 0.3s; }
                    a:hover { background: #4338ca; transform: translateY(-2px); }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Oops!</h1>
                    <p>Our servers encountered an unexpected glitch. Our engineers have been notified and are on it.<br><br>Don't worry, your data is safe.</p>
                    <a href="/login">Return to Home</a>
                </div>
            </body>
        </html>
    '''), 500









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


# ==========================================
# ENTERPRISE GOOGLE SHEETS BACKOFF
# ==========================================
import random
from functools import wraps

def with_exponential_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # If it's the last attempt, raise the error
                    if attempt == max_retries - 1:
                        print(f"FAILED after {max_retries} attempts: {func.__name__} - {e}")
                        raise e

                    # Wait before retrying (exponential backoff with jitter)
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
                    print(f"WARN: {func.__name__} failed (attempt {attempt+1}/{max_retries}). Retrying in {delay:.2f}s... Error: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

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

    sheets_schema = {
        'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent', 'password'],
        'videos': ['id', 'date', 'subject', 'drive_link'],
        'subjects': ['id', 'subject_name'],
        'announcements': ['id', 'date', 'message', 'important'],
        'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time', 'score_expiry'],
        'quiz_scores': ['quiz_id', 'student_id', 'student_name', 'score', 'percentage', 'timestamp'],
        'materials': ['id', 'title', 'subject', 'description', 'drive_link'],
        'schedule': ['id', 'date', 'subject', 'start_time', 'end_time', 'note'],
        'student_profiles': ['student_id', 'extra_notes', 'last_active_date'],
        'video_completion': ['date', 'student_id', 'subject', 'video_id', 'completed'],
        'gamification': ['student_id', 'points', 'badges'],
        'leaderboard_cache': ['student_id', 'points', 'rank'],
        'attendance': ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated'],
        'dpp': ['id', 'title', 'subject', 'class', 'description', 'file_url', 'date_uploaded'],
        'dpp_status': ['dpp_id', 'student_id', 'status'],
        'tasks': ['id', 'title', 'description', 'subject', 'class', 'due_date', 'created_date'],
        'task_status': ['task_id', 'student_id', 'status'],
        'student_metrics': ['student_id', 'xp', 'level', 'streak_days', 'last_active_date', 'reputation_score', 'trusted_devices']
    }

    try:
        ws = sh.worksheet(sheet_name)
    except Exception as e:
        print(f"==========================================")
        print(f"Worksheet '{sheet_name}' not found. Creating it now...")
        print(f"==========================================")
        if sheet_name in sheets_schema:
            try:
                ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
                ws.append_row(sheets_schema[sheet_name])
                print(f"SUCCESS: Created '{sheet_name}' and populated headers.")
            except Exception as creation_error:
                if "already exists" in str(creation_error):
                    try:
                        ws = sh.worksheet(sheet_name)
                    except:
                        return None
                else:
                    print(f"FATAL: Failed to create worksheet '{sheet_name}': {creation_error}")
                    return None
        else:
            print(f"ERROR: Unknown sheet schema requested: {sheet_name}")
            return None

    try:
        if len(ws.get_all_values()) == 0:
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




# ==========================================
# ENTERPRISE XSS SANITIZATION
# ==========================================
import html

def sanitize_input(data):
    if isinstance(data, str):
        return html.escape(data.strip())
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(i) for i in data]
    return data

@with_exponential_backoff(max_retries=3)
def add_data_to_sheet(sheet_name, row_dict):
    try:
        row_dict = sanitize_input(row_dict) # XSS protection
        sheet = get_google_sheet(sheet_name)
        if sheet:
            # We must map the dictionary to a list of values based on the sheet headers
            headers = sheet.row_values(1)
            row_to_insert = [str(row_dict.get(h, '')) for h in headers]
            sheet.append_row(row_to_insert)
            invalidate_cache(sheet_name)
            return True
    except Exception as e:
        print(f"Failed to add data to {sheet_name} sheet: {e}")
    return False

def delete_data_from_sheet(sheet_name, row_id):
    try:
        row_dict = sanitize_input(row_dict) # XSS protection
        sheet = get_google_sheet(sheet_name)
        if sheet:
            records = sheet.get_all_records()
            for index, record in enumerate(records):
                if str(record.get('id', '')) == str(row_id):
                    # +2 because gspread is 1-indexed, and row 1 is headers
                    sheet.delete_rows(index + 2)
                    invalidate_cache(sheet_name)
                    return True
    except Exception as e:
        print(f"Failed to delete data from {sheet_name} sheet: {e}")
    return False


# --- Global Cache for Performance ---
# To avoid hitting Google Sheets API (which is very slow) on every page load,
# we cache the data in memory. The cache is automatically invalidated when data is updated.
import time
DATA_CACHE = {}
CACHE_TTL = 300 # 5 minutes

def get_data(sheet_name):
    # Check cache first
    now = time.time()
    if sheet_name in DATA_CACHE:
        cache_entry = DATA_CACHE[sheet_name]
        if now - cache_entry['timestamp'] < CACHE_TTL:
            return cache_entry['data']

    # If not in cache or expired, fetch from Google Sheets
    sheet = get_google_sheet(sheet_name)
    if sheet:
        try:
            records = sheet.get_all_records()
            # Store in cache
            DATA_CACHE[sheet_name] = {
                'timestamp': now,
                'data': records
            }
            return records
        except Exception as e:
            print(f"Error reading records from {sheet_name}: {e}")
            # If fetch fails but we have stale cache, return stale cache to prevent crashing
            if sheet_name in DATA_CACHE:
                return DATA_CACHE[sheet_name]['data']
            return []
    else:
        print(f"Failed to access Google Sheet '{sheet_name}'. Ensure tab exists and permissions are granted.")
        return []


import threading

def background_refresh():
    try:
        # Silently fetch latest data to update cache behind the scenes
        print("Starting silent background refresh for all V2 sheets...")
        sheets_to_refresh = ['attendance', 'dpp', 'tasks']
        for s in sheets_to_refresh:
            sheet = get_google_sheet(s)
            if sheet:
                records = sheet.get_all_records()
                DATA_CACHE[s] = {
                    'timestamp': time.time(),
                    'data': records
                }
                print(f"Refreshed cache for {s}")
    except Exception as e:
        print(f"Background refresh failed: {e}")

def refresh_local_cache():
    threading.Thread(target=background_refresh).start()

def invalidate_cache(sheet_name):
    if sheet_name in DATA_CACHE:
        del DATA_CACHE[sheet_name]


# --- Decorators for Authentication ---

# ==========================================
# ENTERPRISE RATE LIMITING
# ==========================================
import time

# Simple in-memory rate limiter dictionary: {ip_address: [timestamp1, timestamp2, ...]}
rate_limit_cache = {}
RATE_LIMIT_MAX_REQUESTS = 50
RATE_LIMIT_WINDOW_SECONDS = 60

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        now = time.time()

        # Initialize or clean up old timestamps
        if client_ip not in rate_limit_cache:
            rate_limit_cache[client_ip] = []

        rate_limit_cache[client_ip] = [ts for ts in rate_limit_cache[client_ip] if now - ts < RATE_LIMIT_WINDOW_SECONDS]

        # Check limit
        if len(rate_limit_cache[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Too many requests. Please slow down.'}), 429
            return render_template_string('''
                <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
                <h1>429 Too Many Requests</h1><p>You have exceeded the rate limit. Please try again in a minute.</p>
                </body></html>
            '''), 429

        rate_limit_cache[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

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


def normalize_class(value):
    if not value: return "all"
    return str(value).strip().lower().replace("class", "").replace("th", "").strip()

def class_matches(student_c, target_c):
    norm_s = normalize_class(student_c)
    norm_t = normalize_class(target_c)

    # 10th specific fallback logic
    allowed_10th = ["10", "all", ""]
    if norm_t in allowed_10th: return True
    if norm_s == norm_t: return True

    return False


# --- Gamification Helpers ---
def bulk_award_points(student_points_dict, reason=""):
    # Accepts a dict of {student_id: points_to_add}
    if not student_points_dict: return

    try:
        gamification = get_data('gamification')
        sheet = get_google_sheet('gamification')
        if not sheet: return

        # Build map
        record_map = {str(rec.get('student_id')): rec for rec in gamification if rec.get('student_id')}

        for s_id, pts in student_points_dict.items():
            s_id = str(s_id)
            if s_id in record_map:
                record_map[s_id]['points'] = int(record_map[s_id].get('points') or 0) + pts
            else:
                record_map[s_id] = {'student_id': s_id, 'points': pts, 'badges': ""}

        # Write back gamification
        headers = ['student_id', 'points', 'badges']
        new_data = [headers]
        for key, rec in record_map.items():
            new_data.append([str(rec.get(h, '')) for h in headers])

        sheet.clear()
        sheet.update(new_data)
        invalidate_cache('gamification')

        # Now bulk check badges
        bulk_check_badges(list(student_points_dict.keys()))
        update_leaderboard_cache()

    except Exception as e:
        print(f"Failed to bulk award points: {e}")

def bulk_check_badges(student_ids):
    try:
        videos = get_data('video_completion')
        gamification = get_data('gamification')
        sheet = get_google_sheet('gamification')
        if not sheet: return

        record_map = {str(rec.get('student_id')): rec for rec in gamification if rec.get('student_id')}
        changed = False

        for s_id in student_ids:
            s_id = str(s_id)
            if s_id not in record_map: continue

            completed_videos = len([v for v in videos if str(v.get('student_id')) == s_id])

            badges = str(record_map[s_id].get('badges') or "")
            badges_list = [b.strip() for b in badges.split(",") if b.strip()]

            if "Video Master" not in badges_list and completed_videos >= 10:
                badges_list.append("Video Master")
                record_map[s_id]['badges'] = ", ".join(badges_list)
                changed = True

        if changed:
            headers = ['student_id', 'points', 'badges']
            new_data = [headers]
            for key, rec in record_map.items():
                new_data.append([str(rec.get(h, '')) for h in headers])
            sheet.clear()
            sheet.update(new_data)
            invalidate_cache('gamification')
    except Exception as e:
        print(f"Failed bulk check badges: {e}")

def award_points(student_id, points_to_add, reason=""):
    # Legacy wrapper for single user calls (like quiz or video complete)
    bulk_award_points({str(student_id): points_to_add}, reason)

def update_leaderboard_cache():
    try:
        gamification = get_data('gamification')
        sheet = get_google_sheet('leaderboard_cache')
        if not sheet: return

        sorted_students = sorted(gamification, key=lambda x: int(x.get('points', 0)), reverse=True)

        sheet.clear()

        rows = [['student_id', 'points', 'rank']]
        for rank, student in enumerate(sorted_students, 1):
            rows.append([student.get('student_id'), student.get('points'), rank])

        sheet.update(rows)
        invalidate_cache('leaderboard_cache')

    except Exception as e:
        print(f"Failed to update leaderboard cache: {e}")


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
@rate_limit
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        if role == 'teacher':
            # Hardcoded single admin teacher as requested
            if username == 'admin' and password == 'admin':
                session.permanent = True
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
                session.permanent = True
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
    attendance = get_data('attendance')

    current_date = datetime.now().strftime('%Y-%m-%d')
    today_attendance_count = len([a for a in attendance if a.get('date') == current_date and a.get('status') == 'Present'])

    # Calculate lowest/highest attendance
    student_attendance = {}
    for s in students:
        student_attendance[str(s.get('id'))] = {'name': s.get('name'), 'present': 0, 'total': 0}

    for a in attendance:
        sid = str(a.get('student_id'))
        if sid in student_attendance:
            student_attendance[sid]['total'] += 1
            if a.get('status') == 'Present':
                student_attendance[sid]['present'] += 1

    lowest_student = "N/A"
    highest_student = "N/A"
    lowest_rate = 101
    highest_rate = -1

    for sid, data in student_attendance.items():
        if data['total'] > 0:
            rate = (data['present'] / data['total']) * 100
            if rate < lowest_rate:
                lowest_rate = rate
                lowest_student = f"{data['name']} ({round(rate)}%)"
            if rate > highest_rate:
                highest_rate = rate
                highest_student = f"{data['name']} ({round(rate)}%)"

    if lowest_rate == 101: lowest_student = "No data"
    if highest_rate == -1: highest_student = "No data"

    # Latest video subject
    latest_video_subject = videos[-1].get('subject') if videos else "No videos yet"

    stats = {
        'total_students': len(students),
        'today_attendance': today_attendance_count,
        'lowest_attendance': lowest_student,
        'highest_attendance': highest_student,
        'latest_video': latest_video_subject
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/teacher/students')
@login_required(role='teacher')
def teacher_students():
    students = get_data('students')
    return render_template('students.html', students=students)

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
    refresh_local_cache()
    refresh_local_cache()
    return redirect(url_for('teacher_students'))

@app.route('/teacher/delete_student/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_student(id):
    delete_data_from_sheet('students', id)
    flash('Student deleted successfully!', 'success')
    refresh_local_cache()
    refresh_local_cache()
    return redirect(url_for('teacher_students'))

@app.route('/teacher/attendance')
@login_required(role='teacher')
def teacher_attendance():
    students = get_data('students')
    attendance = get_data('attendance')
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Calculate today's absentees
    absent_students = []
    for a in attendance:
        if a.get('date') == current_date and a.get('status') == 'Absent':
            s_name = next((s.get('name') for s in students if str(s.get('id')) == str(a.get('student_id'))), 'Unknown')
            absent_students.append(s_name)

    import urllib.parse
    wa_text = "Ashwathama Classes:\n\nToday's Absentees (" + current_date + "):\n"
    if absent_students:
        for idx, name in enumerate(absent_students, 1):
            wa_text += f"{idx}. {name}\n"
    else:
        wa_text += "No absentees today! (Or attendance not marked yet)\n"

    wa_link = "https://wa.me/?text=" + urllib.parse.quote(wa_text)

    return render_template('attendance.html', students=students, current_date=current_date, wa_link=wa_link, absent_count=len(absent_students))


import threading

@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('attendance')
    if not sheet:
        return jsonify({'success': False, 'error': "Could not connect to Google Sheet"})

    try:
        from datetime import datetime
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        all_records = sheet.get_all_records()
        headers = sheet.row_values(1)
        if not headers:
            headers = ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated']

        students_info = {str(s.get('id')): s for s in get_data('students')}

        record_map = {}
        for r in all_records:
            key = f"{r.get('student_id')}_{r.get('date')}"
            record_map[key] = r

        points_to_award = {}
        for record in records:
            s_id = str(record['student_id'])
            status = '1' if record['status'] == 'Present' else '0'
            s_name = students_info.get(s_id, {}).get('name', 'Unknown')
            s_class = students_info.get(s_id, {}).get('class', '')

            key = f"{s_id}_{date}"

            if key in record_map:
                record_map[key]['status'] = status
                record_map[key]['last_updated'] = last_updated
                record_map[key]['student_name'] = s_name
                record_map[key]['class'] = s_class
            else:
                record_map[key] = {
                    'student_id': s_id,
                    'student_name': s_name,
                    'class': s_class,
                    'date': date,
                    'status': status,
                    'last_updated': last_updated
                }

            if status == '1':
                # We will collect this and do it in bulk later
                points_to_award[s_id] = 5

        new_sheet_data = [headers]
        for key, rec in record_map.items():
            row = [str(rec.get(h, '')) for h in headers]
            new_sheet_data.append(row)

        sheet.clear()
        sheet.update(new_sheet_data)

        if points_to_award:
            bulk_award_points(points_to_award, "Attendance")

        invalidate_cache('attendance')
        refresh_local_cache()

        return jsonify({'success': True, 'message': 'Attendance saved successfully'})
    except Exception as e:
        print(f"Failed to save Attendance_V2: {e}")
        return jsonify({'success': False, 'error': str(e)})

    else:
        return jsonify({'success': False, 'error': 'Cannot save: Sheet not found'})

@app.route('/teacher/videos')
@login_required(role='teacher')
def teacher_videos():
    videos = get_data('videos')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('videos.html', videos=videos, current_date=current_date)

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
    return render_template('subjects.html', subjects=subjects)

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
    return render_template('announcements.html', announcements=announcements[::-1], current_date=current_date)

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



# --- API Endpoints for AI Features (Teacher) ---












# --- Additional Rendering Routes ---
@app.route('/teacher/ai_tools')
@login_required(role='teacher')
def teacher_ai_tools():
    return render_template('ai_tools.html')

@app.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')

    # Calculate attendance percentage
    attendance_data = get_data('attendance')
    attendance_records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]
    total = len(attendance_records)
    present = len([a for a in attendance_records if str(a.get('status')) in ['1', 'Present']])
    attendance_percentage = round((present / total) * 100) if total > 0 else 0

    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    today_video = next((v for v in videos[::-1] if v.get('date') == current_date), None)
    latest_announcement = announcements[-1] if announcements else None

    data = {
        'attendance_percentage': attendance_percentage,
        'today_video': today_video,
        'latest_announcement': latest_announcement
    }
    return render_template('student_dashboard.html', data=data)

@app.route('/student/my_videos')
@login_required(role='student')
def student_my_videos():
    videos = get_data('videos')
    return render_template('my_videos.html', videos=videos[::-1])

@app.route('/student/attendance')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')
    attendance_data = get_data('attendance')
    attendance_records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]

    total = len(attendance_records)
    present = len([a for a in attendance_records if str(a.get('status')) in ['1', 'Present']])
    absent = total - present
    percentage = round((present / total) * 100) if total > 0 else 0

    formatted_records = []
    for rec in attendance_records[::-1]:
        status_val = str(rec.get('status'))
        formatted_records.append({
            'date': rec.get('date'),
            'status': 'Present' if status_val in ['1', 'Present'] else 'Absent'
        })

    return render_template('attendance_view.html',
                           attendance_records=formatted_records,
                           total_classes=total,
                           present_count=present,
                           absent_count=absent,
                           attendance_percentage=percentage)

@app.route('/student/announcements')
@login_required(role='student')
def student_announcements_view():
    announcements = get_data('announcements')
    return render_template('announcements_view.html', announcements=announcements[::-1])

@app.route('/old_student_chatbot')
@login_required(role='student')
def old_student_chatbot():
    return render_template('chatbot.html')


# --- API Endpoints for AI Features ---
from openai import OpenAI
import os

@app.route('/api/ai/chat', methods=['POST'])
@login_required(role='student')
def ai_chat():
    data = request.json
    messages = data.get('messages', [])
    mode = data.get('mode', 'doubt_solver') # doubt_solver or study_chatbot

    if not messages:
        return jsonify({'success': False, 'error': 'No messages provided'})

    # System prompts based on requirements
    if mode == 'doubt_solver':
        system_prompt = "Explain this concept in very simple words for a school student. If it is a math question, give a step by step solution."
    else:
        system_prompt = "You are a friendly tutor. Help the student with concept doubts, exam preparation, and study tips."

    api_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages
        )
        reply = response.choices[0].message.content
        return jsonify({'success': True, 'reply': reply})
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/attendance', methods=['POST'])
@login_required(role='teacher')
def ai_attendance_analysis():
    attendance_data = get_data('attendance')
    students_data = get_data('students')

    # Process raw data to summarize attendance per student
    student_map = {str(s.get('id')): s.get('name') for s in students_data}
    summary = {}

    for record in attendance_data:
        sid = str(record.get('student_id'))
        status = str(record.get('status'))
        if sid not in summary:
            summary[sid] = {'name': student_map.get(sid, 'Unknown'), 'present': 0, 'total': 0}

        summary[sid]['total'] += 1
        if status in ['1', 'Present']:
            summary[sid]['present'] += 1

    prompt = "Analyze attendance data and provide insights. Which students are irregular? Give attendance percentage. Suggest actions.\nData:\n"
    for sid, data in summary.items():
        if data['total'] > 0:
            prompt += f"- {data['name']}: {data['present']}/{data['total']} present ({int(data['present']/data['total']*100)}%)\n"

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'analysis': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/video_summary', methods=['POST'])
@login_required(role='teacher')
def ai_video_summary():
    topic = request.json.get('topic')
    prompt = f"Generate summary notes for revision for the topic: {topic}. Include summary, key points, and revision notes."

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'summary': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/quiz', methods=['POST'])
@login_required(role='teacher')
def ai_quiz_generator():
    subject = request.json.get('subject')
    topic = request.json.get('topic')
    prompt = f"Generate 5 MCQ questions with answers for the subject '{subject}' and topic '{topic}'. Format as JSON array of objects with keys: question, option1, option2, option3, option4, answer."

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        # Parse the JSON response
        import json
        result = json.loads(response.choices[0].message.content)
        questions = result.get('questions', [])
        # If the API returns it differently, try to adapt or just return the raw array
        if not questions and isinstance(result, list):
            questions = result
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/announcement', methods=['POST'])
@login_required(role='teacher')
def ai_announcement():
    topic = request.json.get('topic')
    prompt = f"Write a professional coaching class announcement about: {topic}"

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({'success': True, 'announcement': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
