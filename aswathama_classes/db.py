import gspread
from google.oauth2.service_account import Credentials
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Define the scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Fetch sheet name from environment
SHEET_NAME = os.getenv("SHEET_NAME", "ASWATHAMA_CLASSES_DB")

class GoogleSheetsDB:
    def __init__(self):
        self.client = None
        self.sheet = None
        self._connect()

    def _connect(self):
        """Connect to Google Sheets using the service account credentials."""
        try:
            # We mock the connection if the credentials file doesn't exist or is dummy,
            # for testing without real credentials.
            if os.path.exists('CREDENTIALS.JSON'):
                import json
                with open('CREDENTIALS.JSON', 'r') as f:
                    creds_data = json.load(f)

                # Simple check to see if it's our dummy file
                if creds_data.get('project_id') == 'dummy-project':
                    self.mock_mode = True
                    self._setup_mock_db()
                    return

            creds = Credentials.from_service_account_file('CREDENTIALS.JSON', scopes=SCOPES)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open(SHEET_NAME)
            self.mock_mode = False
        except Exception as e:
            print(f"Warning: Could not connect to real Google Sheets ({e}). Using mock DB.")
            self.mock_mode = True
            self._setup_mock_db()

    def _setup_mock_db(self):
        """Setup an in-memory mock database for testing when credentials aren't available."""
        self.mock_db = {
            "students": [],
            "attendance": [],
            "videos": [],
            "subjects": [],
            "announcements": []
        }

    def _get_worksheet(self, title):
        if self.mock_mode:
            return self.mock_db.get(title, [])
        try:
            return self.sheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Worksheet {title} not found.")
            return None

    # --- Student Management ---

    def get_all_students(self):
        if self.mock_mode:
            return self.mock_db["students"]
        worksheet = self._get_worksheet("students")
        if not worksheet: return []
        # Return all records as a list of dicts
        try:
            return worksheet.get_all_records()
        except Exception:
            return []

    def get_student_by_id(self, student_id):
        students = self.get_all_students()
        for s in students:
            if str(s.get("id")) == str(student_id):
                return s
        return None

    def add_student(self, data):
        """
        data: dict with name, class, roll, phone, email, parent
        """
        new_id = str(uuid.uuid4())[:8] # Generate a short unique ID
        row = [
            new_id,
            data.get('name', ''),
            data.get('class', ''),
            data.get('roll', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('parent', '')
        ]

        if self.mock_mode:
            self.mock_db["students"].append({
                "id": row[0], "name": row[1], "class": row[2],
                "roll": row[3], "phone": row[4], "email": row[5], "parent": row[6]
            })
            return new_id

        worksheet = self._get_worksheet("students")
        if worksheet:
            worksheet.append_row(row)
            return new_id
        return None

    def delete_student(self, student_id):
        if self.mock_mode:
            self.mock_db["students"] = [s for s in self.mock_db["students"] if str(s["id"]) != str(student_id)]
            return True

        worksheet = self._get_worksheet("students")
        if not worksheet: return False

        try:
            records = worksheet.get_all_records()
            for idx, record in enumerate(records):
                if str(record.get('id')) == str(student_id):
                    worksheet.delete_rows(idx + 2) # +2 because index is 0-based and row 1 is headers
                    return True
        except Exception:
            pass
        return False

    # --- Attendance Management ---

    def mark_attendance(self, date, student_id, status):
        """status: 'Present' or 'Absent'"""
        row = [date, str(student_id), status]
        if self.mock_mode:
            # Update if already exists for this date and student
            for att in self.mock_db["attendance"]:
                if att["date"] == date and att["student_id"] == str(student_id):
                    att["status"] = status
                    return True
            # Otherwise append
            self.mock_db["attendance"].append({
                "date": row[0], "student_id": row[1], "status": row[2]
            })
            return True

        worksheet = self._get_worksheet("attendance")
        if not worksheet: return False

        # Check if already exists and update
        records = worksheet.get_all_records()
        for idx, record in enumerate(records):
            if str(record.get('date')) == date and str(record.get('student_id')) == str(student_id):
                worksheet.update_cell(idx + 2, 3, status)
                return True

        # Append new
        worksheet.append_row(row)
        return True

    def get_attendance_by_date(self, date):
        if self.mock_mode:
            return [a for a in self.mock_db["attendance"] if a["date"] == date]

        worksheet = self._get_worksheet("attendance")
        if not worksheet: return []
        records = worksheet.get_all_records()
        return [r for r in records if str(r.get('date')) == date]

    def get_attendance_for_student(self, student_id):
        if self.mock_mode:
            return [a for a in self.mock_db["attendance"] if str(a["student_id"]) == str(student_id)]

        worksheet = self._get_worksheet("attendance")
        if not worksheet: return []
        records = worksheet.get_all_records()
        return [r for r in records if str(r.get('student_id')) == str(student_id)]

    def get_all_attendance(self):
        if self.mock_mode:
            return self.mock_db["attendance"]
        worksheet = self._get_worksheet("attendance")
        if not worksheet: return []
        return worksheet.get_all_records()

    # --- Video Management ---

    def add_video(self, date, subject, drive_link):
        row = [date, subject, drive_link]
        if self.mock_mode:
            self.mock_db["videos"].append({
                "date": date, "subject": subject, "drive_link": drive_link
            })
            return True

        worksheet = self._get_worksheet("videos")
        if worksheet:
            worksheet.append_row(row)
            return True
        return False

    def get_all_videos(self):
        if self.mock_mode:
            return self.mock_db["videos"]
        worksheet = self._get_worksheet("videos")
        if not worksheet: return []
        return worksheet.get_all_records()

    # --- Subject Management ---

    def add_subject(self, subject_name):
        if self.mock_mode:
            self.mock_db["subjects"].append({"subject_name": subject_name})
            return True

        worksheet = self._get_worksheet("subjects")
        if worksheet:
            worksheet.append_row([subject_name])
            return True
        return False

    def get_all_subjects(self):
        if self.mock_mode:
            return self.mock_db["subjects"]
        worksheet = self._get_worksheet("subjects")
        if not worksheet: return []
        return worksheet.get_all_records()

    def delete_subject(self, subject_name):
        if self.mock_mode:
            self.mock_db["subjects"] = [s for s in self.mock_db["subjects"] if s["subject_name"] != subject_name]
            return True

        worksheet = self._get_worksheet("subjects")
        if not worksheet: return False
        try:
            records = worksheet.get_all_records()
            for idx, record in enumerate(records):
                if record.get('subject_name') == subject_name:
                    worksheet.delete_rows(idx + 2)
                    return True
        except Exception:
            pass
        return False

    # --- Announcement Management ---

    def add_announcement(self, date, message):
        if self.mock_mode:
            self.mock_db["announcements"].append({"date": date, "message": message})
            return True

        worksheet = self._get_worksheet("announcements")
        if worksheet:
            worksheet.append_row([date, message])
            return True
        return False

    def get_all_announcements(self):
        if self.mock_mode:
            return self.mock_db["announcements"]
        worksheet = self._get_worksheet("announcements")
        if not worksheet: return []
        return worksheet.get_all_records()


# Initialize a global instance
db = GoogleSheetsDB()
