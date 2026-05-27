# ASWATHAMA CLASSES

ASWATHAMA CLASSES is a complete AI-powered web platform built with Flask, Google Sheets API, and OpenAI's ChatGPT API. It features a modern SaaS UI and separate dashboards for Teachers (Admin) and Students.

## Setup Guide

### 1. How to create a Google Sheet
- Create a new Google Sheet on your Google Drive.
- Create the following sheets exactly as named:
  - `students`: id, name, class, roll, phone, email, parent, password
  - `attendance`: date, student_id, status
  - `videos`: id, date, subject, drive_link
  - `subjects`: id, subject_name
  - `announcements`: id, date, message, important
  - `quiz`: id, date, subject, question, option1, option2, option3, option4, answer, start_time, end_time, score_expiry
  - `quiz_scores_V3`: quiz_id, student_id, student_name, score, percentage, timestamp
  - `materials`: id, title, subject, description, drive_link
  - `schedule`: id, date, subject, start_time, end_time, note
  - `student_profiles`: student_id, extra_notes, last_active_date
  - `video_completion_V3`: date, student_id, subject, video_id, completed
  - `gamification_V3`: student_id, points, badges
  - `leaderboard_cache_V3`: student_id, points, rank
  - `ATTENDANCE_V2`: student_id, student_name, class, date, status, last_updated
  - `DPP_V2`: id, title, subject, class, description, file_url, date_uploaded
  - `DPP_Status_V3`: dpp_id, student_id, status
  - `TASKS_V2`: id, title, description, subject, class, due_date, created_date
  - `Task_Status_V3`: task_id, student_id, status
  - `Student_Metrics_V3`: student_id, xp, level, streak_days, last_active_date, reputation_score, trusted_devices

### 2. How to enable Sheets API
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Go to "APIs & Services" > "Library".
- Search for "Google Sheets API" and enable it.
- Go to "Credentials" and click "Create Credentials" > "Service Account".
- Fill in the details and create the account.
- Once created, go to the "Keys" tab for the service account, click "Add Key" > "Create new key", and choose JSON.
- Download the JSON file.
- **IMPORTANT**: Share your Google Sheet with the email address of the service account you just created, and give it "Editor" access.

### 3. Where to place the JSON key
- Rename the downloaded JSON file to `credentials.json` (or `CREDENTIALS.JSON`).
- Place it in the root directory of this project.

### 4. Where to place the OpenAI API key
- Create a `.env` file in the root directory of this project.
- Add your OpenAI API key to the `.env` file like this:
  `OPENAI_API_KEY=your_openai_api_key_here`
- Also add your spreadsheet ID to the `.env` file:
  `SPREADSHEET_ID=your_google_sheet_id_here`
- Optional: add `SECRET_KEY=your_flask_secret_key`

### 5. How to run Flask locally
- Ensure you have Python installed.
- Install dependencies: `pip install -r requirements.txt`
- Run the app: `gunicorn app:app --bind 127.0.0.1:5000` or `python app.py`

### 6. How to deploy on Render
- Create an account on [Render](https://render.com/).
- Click "New +" and select "Web Service".
- Connect your GitHub repository containing this code.
- Set the Build Command to `pip install -r requirements.txt`
- Set the Start Command to `gunicorn app:app`
- In the "Environment" section, add the following variables:
  - `OPENAI_API_KEY`: Your OpenAI API key
  - `SPREADSHEET_ID`: Your Google Sheet ID
  - `SECRET_KEY`: A random secret key for Flask sessions
  - `GOOGLE_CREDENTIALS`: Paste the entire contents of your `credentials.json` file here. (The code is set up to read from this environment variable if it exists).
- Deploy!
