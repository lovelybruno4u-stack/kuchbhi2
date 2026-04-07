import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_FILE = 'CREDENTIALS.JSON'
# You would put your sheet ID or Name here. In a real app it's better in .env
# We'll try to open by title 'ASWATHAMA_DB' if available, otherwise fallback.
SHEET_TITLE = 'ASWATHAMA_DB'

class Database:
    def __init__(self):
        self.use_mock = False
        self.client = None
        self.sheet = None

        self.mock_db = {
            'students': [
                {'id': '1', 'name': 'John Doe', 'class': '10', 'roll': '101', 'phone': '1234567890', 'email': 'john@example.com', 'parent': 'Mr. Doe'},
                {'id': '2', 'name': 'Jane Smith', 'class': '10', 'roll': '102', 'phone': '0987654321', 'email': 'jane@example.com', 'parent': 'Mrs. Smith'}
            ],
            'attendance': [
                {'date': '2023-10-01', 'student_id': '1', 'status': 'present'},
                {'date': '2023-10-01', 'student_id': '2', 'status': 'absent'}
            ],
            'videos': [
                {'date': '2023-10-01', 'subject': 'Math', 'drive_link': 'https://drive.google.com/test1'}
            ],
            'subjects': [
                {'subject_name': 'Math'},
                {'subject_name': 'Science'}
            ],
            'announcements': [
                {'date': '2023-10-01', 'message': 'Holiday tomorrow!'}
            ]
        }

        try:
            if os.path.exists(CREDENTIALS_FILE):
                # Check if it has content
                with open(CREDENTIALS_FILE, 'r') as f:
                    content = f.read().strip()
                if content and content != '{}':
                    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
                    self.client = gspread.authorize(creds)
                    self.sheet = self.client.open(SHEET_TITLE)
                    print("Successfully connected to Google Sheets.")
                else:
                    print("CREDENTIALS.JSON is empty or invalid. Using mock database.")
                    self.use_mock = True
            else:
                print("CREDENTIALS.JSON not found. Using mock database.")
                self.use_mock = True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}. Using mock database.")
            self.use_mock = True

    def get_sheet_records(self, sheet_name):
        if self.use_mock:
            return self.mock_db.get(sheet_name, [])
        try:
            worksheet = self.sheet.worksheet(sheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            print(f"Error fetching from {sheet_name}: {e}")
            return []

    def append_row(self, sheet_name, row_values):
        if self.use_mock:
            # Need to match headers for mock
            headers = self._get_headers(sheet_name)
            record = dict(zip(headers, row_values))
            self.mock_db.setdefault(sheet_name, []).append(record)
            return True
        try:
            worksheet = self.sheet.worksheet(sheet_name)
            worksheet.append_row(row_values)
            return True
        except Exception as e:
            print(f"Error appending to {sheet_name}: {e}")
            return False

    def update_row(self, sheet_name, match_col, match_val, new_values_dict):
        """Update a row based on a match in a specific column."""
        if self.use_mock:
            for item in self.mock_db.get(sheet_name, []):
                if str(item.get(match_col)) == str(match_val):
                    item.update(new_values_dict)
                    return True
            return False

        try:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            for i, record in enumerate(records):
                if str(record.get(match_col)) == str(match_val):
                    row_index = i + 2 # +2 because 1-based and header row

                    headers = worksheet.row_values(1)
                    for key, val in new_values_dict.items():
                        if key in headers:
                            col_index = headers.index(key) + 1
                            worksheet.update_cell(row_index, col_index, val)
                    return True
            return False
        except Exception as e:
            print(f"Error updating {sheet_name}: {e}")
            return False

    def delete_row(self, sheet_name, match_col, match_val):
        if self.use_mock:
            original_len = len(self.mock_db.get(sheet_name, []))
            self.mock_db[sheet_name] = [item for item in self.mock_db.get(sheet_name, []) if str(item.get(match_col)) != str(match_val)]
            return len(self.mock_db[sheet_name]) < original_len

        try:
            worksheet = self.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            for i, record in enumerate(records):
                if str(record.get(match_col)) == str(match_val):
                    row_index = i + 2
                    worksheet.delete_rows(row_index)
                    return True
            return False
        except Exception as e:
            print(f"Error deleting from {sheet_name}: {e}")
            return False

    def _get_headers(self, sheet_name):
        headers_map = {
            'students': ['id', 'name', 'class', 'roll', 'phone', 'email', 'parent'],
            'attendance': ['date', 'student_id', 'status'],
            'videos': ['date', 'subject', 'drive_link'],
            'subjects': ['subject_name'],
            'announcements': ['date', 'message']
        }
        return headers_map.get(sheet_name, [])

db = Database()
