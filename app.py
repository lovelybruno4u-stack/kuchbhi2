import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')






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

    sheets_schema = {
        'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent', 'password'],
        'attendance': ['date', 'student_id', 'status'],
        'videos': ['id', 'date', 'subject', 'drive_link'],
        'subjects': ['id', 'subject_name'],
        'announcements': ['id', 'date', 'message', 'important'],
        'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer'],
        'materials': ['id', 'title', 'subject', 'description', 'drive_link'],
        'schedule': ['id', 'date', 'subject', 'start_time', 'end_time', 'note'],
        'student_profiles': ['student_id', 'extra_notes', 'last_active_date'],
        'video_completion': ['date', 'student_id', 'subject', 'completed'],
        'gamification': ['student_id', 'points', 'badges'],
        'leaderboard_cache': ['student_id', 'points', 'rank'],
        'Attendance_V2': ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated'],
        'DPP': ['id', 'title', 'subject', 'class', 'description', 'file_url', 'date_uploaded'],
        'DPP_Status': ['dpp_id', 'student_id', 'status'],
        'Daily_Tasks': ['id', 'title', 'description', 'subject', 'class', 'due_date', 'created_date'],
        'Task_Status': ['task_id', 'student_id', 'status']
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



def add_data_to_sheet(sheet_name, row_dict):
    try:
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

def invalidate_cache(sheet_name):
    if sheet_name in DATA_CACHE:
        del DATA_CACHE[sheet_name]


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

    return render_template('teacher/attendance.html', students=students, current_date=current_date, wa_link=wa_link, absent_count=len(absent_students))

@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('Attendance_V2')
    if not sheet:
        return jsonify({'success': False, 'error': "Could not connect to Google Sheet"})

    try:
        from datetime import datetime
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Read entire sheet
        all_records = sheet.get_all_records()
        headers = sheet.row_values(1)
        if not headers:
            headers = ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated']

        students_info = {str(s.get('id')): s for s in get_data('students')}

        # Convert existing records to a dictionary mapped by "student_id_date"
        record_map = {}
        for r in all_records:
            key = f"{r.get('student_id')}_{r.get('date')}"
            record_map[key] = r

        # Update or Insert incoming records
        for record in records:
            s_id = str(record['student_id'])
            status = '1' if record['status'] == 'Present' else '0'
            s_name = students_info.get(s_id, {}).get('name', 'Unknown')
            s_class = students_info.get(s_id, {}).get('class', '')

            key = f"{s_id}_{date}"

            if key in record_map:
                # Update existing
                record_map[key]['status'] = status
                record_map[key]['last_updated'] = last_updated
                record_map[key]['student_name'] = s_name
                record_map[key]['class'] = s_class
            else:
                # Create new
                record_map[key] = {
                    'student_id': s_id,
                    'student_name': s_name,
                    'class': s_class,
                    'date': date,
                    'status': status,
                    'last_updated': last_updated
                }

            # Give points if present
            if status == '1':
                award_points(s_id, 5, "Attendance")

        # Reconstruct sheet data
        new_sheet_data = [headers]
        for key, rec in record_map.items():
            row = [str(rec.get(h, '')) for h in headers]
            new_sheet_data.append(row)

        # Bulk replace to ensure ZERO duplicates and perfect sync
        sheet.clear()
        sheet.update(new_sheet_data)

        invalidate_cache('Attendance_V2')

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



# --- API Endpoints for AI Features (Teacher) ---











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


# --- DPP Routes ---
@app.route('/teacher/dpp')
@login_required(role='teacher')
def teacher_dpp():
    dpp = get_data('DPP')
    subjects = get_data('subjects')
    return render_template('teacher/dpp.html', dpp=dpp, subjects=subjects)

@app.route('/teacher/add_dpp', methods=['POST'])
@login_required(role='teacher')
def add_dpp():
    import uuid
    from datetime import datetime
    new_dpp = {
        'id': str(uuid.uuid4())[:8],
        'title': request.form.get('title'),
        'subject': request.form.get('subject'),
        'class': request.form.get('student_class'),
        'description': request.form.get('description'),
        'file_url': request.form.get('file_url'),
        'date_uploaded': datetime.now().strftime('%Y-%m-%d')
    }
    add_data_to_sheet('DPP', new_dpp)
    flash('DPP uploaded!', 'success')
    return redirect(url_for('teacher_dpp'))

@app.route('/teacher/delete_dpp/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_dpp(id):
    delete_data_from_sheet('DPP', id)
    flash('DPP deleted!', 'success')
    return redirect(url_for('teacher_dpp'))

# --- Daily Tasks Routes ---
@app.route('/teacher/tasks')
@login_required(role='teacher')
def teacher_tasks():
    tasks = get_data('Daily_Tasks')
    subjects = get_data('subjects')
    return render_template('teacher/tasks.html', tasks=tasks, subjects=subjects)

@app.route('/teacher/add_task', methods=['POST'])
@login_required(role='teacher')
def add_task():
    import uuid
    from datetime import datetime
    new_task = {
        'id': str(uuid.uuid4())[:8],
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'subject': request.form.get('subject'),
        'class': request.form.get('student_class'),
        'due_date': request.form.get('due_date'),
        'created_date': datetime.now().strftime('%Y-%m-%d')
    }
    add_data_to_sheet('Daily_Tasks', new_task)
    flash('Task assigned!', 'success')
    return redirect(url_for('teacher_tasks'))

@app.route('/teacher/delete_task/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_task(id):
    delete_data_from_sheet('Daily_Tasks', id)
    flash('Task deleted!', 'success')
    return redirect(url_for('teacher_tasks'))

@app.route('/api/student/complete_task', methods=['POST'])
@login_required(role='student')
def complete_task():
    student_id = session.get('student_id')
    data = request.json
    task_id = data.get('task_id')

    new_status = {
        'task_id': task_id,
        'student_id': student_id,
        'status': 'Completed'
    }
    add_data_to_sheet('Task_Status', new_status)
    award_points(student_id, 5, "Completed Daily Task")

    return jsonify({'success': True, 'points_earned': 5})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# --- Student Specific Backend Routes ---
@app.route('/student/dashboard', endpoint='student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')
    subjects = get_data('subjects')

    # Safely fetch attendance and calculate rate
    attendance_data = get_data('attendance')
    if attendance_data:
        attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]
    else:
        attendance = []

    total = len(attendance) if attendance else 1
    present = len([a for a in attendance if a.get('status') == 'Present'])
    attendance_percentage = round((present / total) * 100) if len(attendance) > 0 else 0

    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')

    today_video = None
    if videos:
        for v in videos[::-1]:
            if v.get('date') == current_date:
                today_video = v
                break

    latest_announcement = announcements[-1] if announcements else None

    # Get Leaderboard Cache
    leaderboard = get_data('leaderboard_cache')
    top_students = []

    # Join with students list for names
    all_students = get_data('students')
    student_names = {str(s.get('id')): s.get('name') for s in all_students}

    for entry in leaderboard[:5]: # Top 5 only
        entry['name'] = student_names.get(str(entry.get('student_id')), "Unknown Student")
        top_students.append(entry)

    data = {
        'attendance_percentage': attendance_percentage,
        'today_video': today_video,
        'latest_announcement': latest_announcement,
        'subjects': subjects,
        'leaderboard': top_students
    }

    return render_template('student/student_dashboard.html', data=data)

@app.route('/student/leaderboard')
@login_required(role='student')
def student_leaderboard():
    leaderboard = get_data('leaderboard_cache')
    all_students = get_data('students')
    student_names = {str(s.get('id')): s.get('name') for s in all_students}

    top_students = []
    for entry in leaderboard:
        entry['name'] = student_names.get(str(entry.get('student_id')), "Unknown Student")
        top_students.append(entry)

    return render_template('student/leaderboard.html', leaderboard=top_students)


@app.route('/student/my_videos', endpoint='student_my_videos')
@login_required(role='student')
def student_my_videos():
    student_id = session.get('student_id')
    videos = get_data('videos')
    completions = get_data('video_completion')

    completed_video_subjects = [c.get('subject') for c in completions if str(c.get('student_id')) == str(student_id)]

    return render_template('student/my_videos.html', videos=videos, completed_video_subjects=completed_video_subjects)

@app.route('/student/attendance', endpoint='student_attendance_view')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')

    # Use Attendance_V2
    attendance_data = get_data('Attendance_V2')

    if attendance_data:
        attendance_records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]
    else:
        attendance_records = []

    total = len(attendance_records)
    # The new Attendance_V2 stores status as binary '1' or '0'
    present = len([a for a in attendance_records if str(a.get('status')) == '1'])
    absent = total - present
    percentage = (present / total) * 100 if total > 0 else 0

    # Map the binary status back to "Present"/"Absent" string for the UI template so we don't have to rewrite the HTML logic
    formatted_records = []
    for rec in attendance_records[::-1]: # reverse chronological
        formatted_records.append({
            'date': rec.get('date'),
            'status': 'Present' if str(rec.get('status')) == '1' else 'Absent'
        })

    return render_template('student/attendance_view.html',
                           attendance_records=formatted_records,
                           total_classes=total,
                           present_count=present,
                           absent_count=absent,
                           attendance_percentage=percentage)

@app.route('/student/announcements', endpoint='student_announcements_view')
@login_required(role='student')
def student_announcements_view():
    announcements = get_data('announcements')
    return render_template('student/announcements_view.html', announcements=announcements[::-1])



# --- API Endpoints for AI Features (Student) ---





# --- Materials Routes ---
@app.route('/teacher/materials')
@login_required(role='teacher')
def teacher_materials():
    materials = get_data('materials')
    subjects = get_data('subjects')
    return render_template('teacher/materials.html', materials=materials, subjects=subjects)

@app.route('/teacher/add_material', methods=['POST'])
@login_required(role='teacher')
def add_material():
    import uuid
    new_mat = {
        'id': str(uuid.uuid4())[:8],
        'title': request.form.get('title'),
        'subject': request.form.get('subject'),
        'description': request.form.get('description'),
        'drive_link': request.form.get('drive_link')
    }
    add_data_to_sheet('materials', new_mat)
    flash('Study material added!', 'success')
    return redirect(url_for('teacher_materials'))

@app.route('/teacher/delete_material/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_material(id):
    delete_data_from_sheet('materials', id)
    flash('Material deleted!', 'success')
    return redirect(url_for('teacher_materials'))

@app.route('/student/materials')
@login_required(role='student')
def student_materials():
    materials = get_data('materials')
    return render_template('student/materials.html', materials=materials)

# --- Schedule Routes ---
@app.route('/teacher/schedule')
@login_required(role='teacher')
def teacher_schedule():
    schedule = get_data('schedule')
    subjects = get_data('subjects')
    # Sort by date
    try:
        schedule = sorted(schedule, key=lambda x: x.get('date', ''))
    except:
        pass
    return render_template('teacher/schedule.html', schedule=schedule, subjects=subjects)

@app.route('/teacher/add_schedule', methods=['POST'])
@login_required(role='teacher')
def add_schedule():
    import uuid
    new_sched = {
        'id': str(uuid.uuid4())[:8],
        'date': request.form.get('date'),
        'subject': request.form.get('subject'),
        'start_time': request.form.get('start_time'),
        'end_time': request.form.get('end_time'),
        'note': request.form.get('note')
    }
    add_data_to_sheet('schedule', new_sched)
    flash('Class scheduled!', 'success')
    return redirect(url_for('teacher_schedule'))

@app.route('/teacher/delete_schedule/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_schedule(id):
    delete_data_from_sheet('schedule', id)
    flash('Class removed from schedule!', 'success')
    return redirect(url_for('teacher_schedule'))

@app.route('/student/schedule')
@login_required(role='student')
def student_schedule():
    schedule = get_data('schedule')
    try:
        schedule = sorted(schedule, key=lambda x: x.get('date', ''))
    except:
        pass
    return render_template('student/schedule.html', schedule=schedule)

# --- Quiz Routes ---
@app.route('/teacher/quiz')
@login_required(role='teacher')
def teacher_quiz():
    quiz_data = get_data('quiz')
    subjects = get_data('subjects')
    try:
        quiz_data = sorted(quiz_data, key=lambda x: x.get('date', ''))
    except:
        pass
    return render_template('teacher/quiz.html', quiz=quiz_data, subjects=subjects)

@app.route('/teacher/add_quiz', methods=['POST'])
@login_required(role='teacher')
def add_quiz():
    import uuid
    new_q = {
        'id': str(uuid.uuid4())[:8],
        'date': request.form.get('date'),
        'subject': request.form.get('subject'),
        'question': request.form.get('question'),
        'option1': request.form.get('option1'),
        'option2': request.form.get('option2'),
        'option3': request.form.get('option3'),
        'option4': request.form.get('option4'),
        'answer': request.form.get('answer')
    }
    add_data_to_sheet('quiz', new_q)
    flash('Quiz question added!', 'success')
    return redirect(url_for('teacher_quiz'))

@app.route('/teacher/delete_quiz/<id>', methods=['POST'])
@login_required(role='teacher')
def delete_quiz(id):
    delete_data_from_sheet('quiz', id)
    flash('Quiz question deleted!', 'success')
    return redirect(url_for('teacher_quiz'))

@app.route('/student/quiz')
@login_required(role='student')
def student_quiz():
    quiz_data = get_data('quiz')
    # Group by subject and date for better UI
    from collections import defaultdict
    quizzes = defaultdict(list)
    for q in quiz_data:
        key = f"{q.get('date', '')} - {q.get('subject', '')}"
        quizzes[key].append(q)
    return render_template('student/quiz.html', quizzes=quizzes)

# --- Profile Routes ---
@app.route('/student/profile', endpoint='student_profile')
@login_required(role='student')
def student_profile():
    student_id = session.get('student_id')
    students = get_data('students')
    student_data = next((s for s in students if str(s.get('id')) == str(student_id)), None)

    if not student_data:
        flash("Profile not found.", "error")
        return redirect(url_for('student_dashboard'))

    attendance_data = get_data('attendance')
    attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]

    total_classes = len(attendance)
    present_classes = len([a for a in attendance if a.get('status') == 'Present'])
    attendance_percentage = round((present_classes / total_classes) * 100) if total_classes > 0 else 0

    subjects = get_data('subjects')
    videos = get_data('videos')

    # Check/Update last active date
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    profiles = get_data('student_profiles')
    profile = next((p for p in profiles if str(p.get('student_id')) == str(student_id)), None)

    extra_notes = profile.get('extra_notes', '') if profile else 'Welcome to your learning journey!'
    last_active = profile.get('last_active_date', current_date) if profile else current_date

    try:
        # Save last active
        sheet = get_google_sheet('student_profiles')
        if sheet:
            if not profile:
                sheet.append_row([student_id, extra_notes, current_date])
                invalidate_cache('student_profiles')
            else:
                # Update existing row logic (simplified to just append for activity logs)
                # If we really want to update, we find the row index.
                records = sheet.get_all_records()
                for i, r in enumerate(records):
                    if str(r.get('student_id')) == str(student_id):
                        sheet.update_cell(i + 2, 3, current_date)
                        invalidate_cache('student_profiles')
                        break
    except Exception as e:
        print(f"Failed to update profile activity: {e}")

    gamification = get_data('gamification')
    leaderboard = get_data('leaderboard_cache')
    video_completion = get_data('video_completion')
    quiz_data = get_data('quiz')

    student_gami = next((g for g in gamification if str(g.get('student_id')) == str(student_id)), None)
    student_rank = next((l for l in leaderboard if str(l.get('student_id')) == str(student_id)), None)

    points = student_gami.get('points', 0) if student_gami else 0
    badges = student_gami.get('badges', '') if student_gami else ""
    rank = student_rank.get('rank', 'N/A') if student_rank else 'N/A'

    completed_vids = len([v for v in video_completion if str(v.get('student_id')) == str(student_id)])

    return render_template('student/profile.html',
                           student=student_data,
                           attendance_percentage=attendance_percentage,
                           total_subjects=len(subjects),
                           total_videos=len(videos),
                           extra_notes=extra_notes,
                           last_active=last_active,
                           points=points,
                           badges=badges,
                           rank=rank,
                           completed_vids=completed_vids,
                           quiz_data=quiz_data)

@app.route('/api/student/submit_quiz', methods=['POST'])
@login_required(role='student')
def submit_quiz():
    student_id = session.get('student_id')
    data = request.json
    percentage = data.get('percentage', 0)

    # +10 for participation
    points_earned = 10

    # Bonus points based on score
    if percentage >= 90:
        points_earned += 50
    elif percentage >= 75:
        points_earned += 30
    elif percentage >= 50:
        points_earned += 15
    else:
        points_earned += 5

    award_points(student_id, points_earned, f"Quiz Attempt ({percentage}%)")

    # Check Quiz Champion badge
    gamification = get_data('gamification')
    sheet = get_google_sheet('gamification')
    if sheet:
        for idx, rec in enumerate(gamification):
            if str(rec.get('student_id')) == str(student_id):
                badges = str(rec.get('badges') or "")
                badges_list = [b.strip() for b in badges.split(",") if b.strip()]
                if "Quiz Champion" not in badges_list:
                    badges_list.append("Quiz Champion")
                    sheet.update_cell(idx + 2, 3, ", ".join(badges_list))
                break

    return jsonify({'success': True, 'points_earned': points_earned})

@app.route('/api/student/mark_video_complete', methods=['POST'])
@login_required(role='student')
def mark_video_complete():
    student_id = session.get('student_id')
    data = request.json
    video_id = data.get('video_id')
    subject = data.get('subject')
    video_date = data.get('video_date')

    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')

    new_completion = {
        'date': current_date,
        'student_id': student_id,
        'subject': subject,
        'completed': 'Yes'
    }

    add_data_to_sheet('video_completion', new_completion)

    points_earned = 10
    if video_date == current_date:
        points_earned += 5 # Same day bonus

    award_points(student_id, points_earned, f"Completed Video: {subject}")

    return jsonify({'success': True, 'points_earned': points_earned})

@app.route('/teacher/dpp_status/<dpp_id>')
@login_required(role='teacher')
def teacher_dpp_status(dpp_id):
    dpps = get_data('DPP')
    dpp = next((d for d in dpps if str(d.get('id')) == str(dpp_id)), None)
    if not dpp:
        flash("DPP not found.", "error")
        return redirect(url_for('teacher_dpp'))

    students = get_data('students')
    dpp_status_data = get_data('DPP_Status')

    # Filter students by class if DPP has a class assigned
    target_class = str(dpp.get('class', ''))
    if target_class:
        filtered_students = [s for s in students if str(s.get('class')).lower() == target_class.lower()]
    else:
        filtered_students = students

    # Get current status
    status_map = {str(d.get('student_id')): str(d.get('status')) for d in dpp_status_data if str(d.get('dpp_id')) == str(dpp_id)}

    for s in filtered_students:
        sid = str(s.get('id'))
        s['completed'] = 1 if status_map.get(sid) == '1' else 0

    return render_template('teacher/dpp_status.html', dpp=dpp, students=filtered_students)

@app.route('/api/teacher/dpp_status', methods=['POST'])
@login_required(role='teacher')
def save_dpp_status():
    data = request.json
    dpp_id = data.get('dpp_id')
    records = data.get('records', [])

    sheet = get_google_sheet('DPP_Status')
    if not sheet:
        return jsonify({'success': False, 'error': "Could not connect to Google Sheet"})

    try:
        all_records = sheet.get_all_records()
        record_map = {}
        for index, r in enumerate(all_records):
            key = f"{r.get('dpp_id')}_{r.get('student_id')}"
            record_map[key] = index + 2

        rows_to_insert = []
        for record in records:
            s_id = str(record['student_id'])
            status = '1' if record['status'] == 'Completed' else '0'
            key = f"{dpp_id}_{s_id}"

            if key in record_map:
                row_idx = record_map[key]
                sheet.delete_rows(row_idx)
                for k in record_map:
                    if record_map[k] > row_idx:
                        record_map[k] -= 1

            rows_to_insert.append([dpp_id, s_id, status])

        if rows_to_insert:
            sheet.append_rows(rows_to_insert)
            invalidate_cache('DPP_Status')

        return jsonify({'success': True})
    except Exception as e:
        print(f"Failed to save DPP_Status: {e}")
        return jsonify({'success': False, 'error': str(e)})
