with open('app.py', 'r') as f:
    content = f.read()

# Add a function to ensure sheets exist inside the existing spreadsheet
ensure_code = """
def get_google_sheet(sheet_name):
    \"\"\"Helper to get a specific worksheet from Google Sheets.
       Automatically creates the worksheet with headers if it doesn't exist.
    \"\"\"
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
"""

# Replace the previous get_google_sheet with this one
import re
old_ggs_regex = re.compile(r'def get_google_sheet\(sheet_name\):.*?return None\n', re.DOTALL)
content = re.sub(old_ggs_regex, ensure_code.strip() + "\n", content)

with open('app.py', 'w') as f:
    f.write(content)
