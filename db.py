import os
import json
import time
import random
from functools import wraps
import threading
import html
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '1h_vz2JXdDX4GDqkQQwr3mQArHMqsYdem7Xjv8KVkrY8')
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
CREDENTIALS_FILE = 'CREDENTIALS.JSON'

DATA_CACHE = {}
CACHE_TTL = 300 # 5 minutes

# MOCK DB FALLBACK
MOCK_MODE = False
MOCK_DB = {}

sheets_schema = {
    'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent', 'password'],
    'videos': ['id', 'date', 'subject', 'drive_link'],
    'subjects': ['id', 'subject_name'],
    'announcements': ['id', 'date', 'message', 'important'],
    'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time', 'score_expiry'],
    'quiz_scores_V3': ['quiz_id', 'student_id', 'student_name', 'score', 'percentage', 'timestamp'],
    'materials': ['id', 'title', 'subject', 'description', 'drive_link'],
    'schedule': ['id', 'date', 'subject', 'start_time', 'end_time', 'note'],
    'student_profiles': ['student_id', 'extra_notes', 'last_active_date'],
    'video_completion_V3': ['date', 'student_id', 'subject', 'video_id', 'completed'],
    'gamification_V3': ['student_id', 'points', 'badges'],
    'leaderboard_cache_V3': ['student_id', 'points', 'rank'],
    'ATTENDANCE_V2': ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated'],
    'DPP_V2': ['id', 'title', 'subject', 'class', 'description', 'file_url', 'date_uploaded'],
    'DPP_Status_V3': ['dpp_id', 'student_id', 'status'],
    'TASKS_V2': ['id', 'title', 'description', 'subject', 'class', 'due_date', 'created_date'],
    'Task_Status_V3': ['task_id', 'student_id', 'status'],
    'Student_Metrics_V3': ['student_id', 'xp', 'level', 'streak_days', 'last_active_date', 'reputation_score', 'trusted_devices']
}

def init_mock_db():
    global MOCK_MODE, MOCK_DB
    MOCK_MODE = True
    print("WARNING: Using in-memory MOCK DB fallback.")
    for sheet, schema in sheets_schema.items():
        MOCK_DB[sheet] = []

def get_gspread_client():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    try:
        if GOOGLE_CREDENTIALS:
            creds_info = json.loads(GOOGLE_CREDENTIALS)
            credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        else:
            if not os.path.exists(CREDENTIALS_FILE) or os.path.getsize(CREDENTIALS_FILE) == 0 or open(CREDENTIALS_FILE).read().strip() == '{}':
                init_mock_db()
                return None
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error authenticating with Google: {e}")
        init_mock_db()
        return None

def with_exponential_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if MOCK_MODE: return func(*args, **kwargs)
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"FAILED after {max_retries} attempts: {func.__name__} - {e}")
                        raise e
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
                    print(f"WARN: {func.__name__} failed. Retrying in {delay:.2f}s... Error: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

def get_google_sheet(sheet_name):
    if MOCK_MODE: return True
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

def sanitize_input(data):
    if isinstance(data, str): return html.escape(data.strip())
    elif isinstance(data, dict): return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list): return [sanitize_input(i) for i in data]
    return data

@with_exponential_backoff(max_retries=3)
def add_data_to_sheet(sheet_name, row_dict):
    try:
        row_dict = sanitize_input(row_dict)
        if MOCK_MODE:
            if sheet_name not in MOCK_DB: MOCK_DB[sheet_name] = []
            MOCK_DB[sheet_name].append(row_dict)
            invalidate_cache(sheet_name)
            return True
        sheet = get_google_sheet(sheet_name)
        if sheet:
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
        if MOCK_MODE:
            if sheet_name in MOCK_DB:
                MOCK_DB[sheet_name] = [r for r in MOCK_DB[sheet_name] if str(r.get('id', '')) != str(row_id)]
                invalidate_cache(sheet_name)
                return True
            return False

        sheet = get_google_sheet(sheet_name)
        if sheet:
            records = sheet.get_all_records()
            for index, record in enumerate(records):
                if str(record.get('id', '')) == str(row_id):
                    sheet.delete_rows(index + 2)
                    invalidate_cache(sheet_name)
                    return True
    except Exception as e:
        print(f"Failed to delete data from {sheet_name} sheet: {e}")
    return False

def get_data(sheet_name):
    now = time.time()
    if sheet_name in DATA_CACHE:
        cache_entry = DATA_CACHE[sheet_name]
        if now - cache_entry['timestamp'] < CACHE_TTL:
            return cache_entry['data']

    if MOCK_MODE:
        records = MOCK_DB.get(sheet_name, [])
        DATA_CACHE[sheet_name] = {'timestamp': now, 'data': records}
        return records

    sheet = get_google_sheet(sheet_name)
    if sheet:
        try:
            records = sheet.get_all_records()
            DATA_CACHE[sheet_name] = {'timestamp': now, 'data': records}
            return records
        except Exception as e:
            print(f"Error reading records from {sheet_name}: {e}")
            if sheet_name in DATA_CACHE: return DATA_CACHE[sheet_name]['data']
            return []
    return []

def invalidate_cache(sheet_name):
    if sheet_name in DATA_CACHE:
        del DATA_CACHE[sheet_name]

def background_refresh():
    try:
        print("Starting silent background refresh for all V2 sheets...")
        sheets_to_refresh = ['ATTENDANCE_V2', 'DPP_V2', 'TASKS_V2']
        for s in sheets_to_refresh:
            get_data(s)
    except Exception as e:
        pass

def refresh_local_cache():
    threading.Thread(target=background_refresh).start()
