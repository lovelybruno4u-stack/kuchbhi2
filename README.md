# Aswathama Classes

ASWATHAMA CLASSES is an AI-powered edtech platform built with Flask, Google Sheets API, and OpenAI.

## Setup Guide

### 1. How to create a Google Sheet
- Go to Google Sheets and create a new spreadsheet.
- Create the following sheets (tabs) EXACTLY with these names:
  1. `students` (Columns: id, name, class, roll, phone, email, parent)
  2. `attendance` (Columns: date, student_id, status)
  3. `videos` (Columns: date, subject, drive_link)
  4. `subjects` (Columns: subject_name)
  5. `announcements` (Columns: date, message)

### 2. How to enable Sheets API
- Go to Google Cloud Console (console.cloud.google.com).
- Create a new project.
- Go to "APIs & Services" > "Library" and search for "Google Sheets API" and "Google Drive API". Enable both.
- Go to "Credentials" > "Create Credentials" > "Service Account".
- Fill in the details and create the service account.
- Add a new key (JSON format) and download it.
- **Important:** Open your Google Sheet, click "Share", and add the service account email (from the JSON file) as an "Editor".

### 3. Where to place JSON Key
- Rename the downloaded JSON file to `CREDENTIALS.JSON`.
- Place it in the root folder of this project (replace the existing empty `CREDENTIALS.JSON`).
- Also, add your Google Sheet ID to `.env` as `SPREADSHEET_ID=<your_sheet_id>`. (The ID is the long string in the sheet URL).

### 4. Where to place OpenAI API Key
- Create a `.env` file in the root directory.
- Add your API key: `OPENAI_API_KEY=your_openai_api_key_here`
- You can also set a custom `FLASK_SECRET_KEY` in `.env`.

### 5. How to run Flask locally
- Install dependencies: `pip install -r requirements.txt`
- Run the app: `gunicorn app:app --bind 127.0.0.1:5000` or `python app.py`

### 6. How to deploy on Render
- Push this code to a GitHub repository.
- Log in to Render (render.com) and create a new "Web Service".
- Connect your GitHub repository.
- Set the Build Command to: `pip install -r requirements.txt`
- Set the Start Command to: `gunicorn app:app --bind 0.0.0.0:$PORT`
- In Render's Environment Variables settings, add:
  - `OPENAI_API_KEY`
  - `FLASK_SECRET_KEY`
  - `SPREADSHEET_ID`
  - Copy the contents of `CREDENTIALS.JSON` into a secret file on Render or set it via environment variables if configured to parse from env. (Note: The simplest is to upload `CREDENTIALS.JSON` as a Secret File and mount it).
