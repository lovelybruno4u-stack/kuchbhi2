import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace all of the DB connection code with a simplified one without auto-setup
new_db_code = """# Google Sheets Setup
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
    \"\"\"Helper to get a specific worksheet from Google Sheets.\"\"\"
    gc = get_gspread_client()
    if not gc:
        return None

    try:
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.worksheet(sheet_name)
    except Exception as e:
        print(f"Error accessing Google Sheets ({sheet_name}): {e}")
        return None
"""

# Find the start and end of the DB code chunk
start_marker = "# Google Sheets Setup"
end_marker = "# MOCK DATA FOR DEVELOPMENT WITHOUT ACTIVE GOOGLE SHEET"

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    content = content[:start_idx] + new_db_code + "\n" + content[end_idx:]

# Remove before_request
setup_hook = """
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
            pass
"""
content = content.replace(setup_hook, "")

# Remove setup route
setup_route_regex = re.compile(r'@app\.route\(\'/setup\'.*?return render_template\(\'setup\.html\'\)', re.DOTALL)
content = re.sub(setup_route_regex, '', content)

with open('app.py', 'w') as f:
    f.write(content)

import os
if os.path.exists('templates/setup.html'):
    os.remove('templates/setup.html')
