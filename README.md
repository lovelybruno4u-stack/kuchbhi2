# Aswathama Classes

AI-powered edtech platform for coaching classes.

## Features
- Teacher Dashboard & Student Dashboard
- AI Doubt Solver & Study Chatbot
- AI Quiz Generator, Video Summary, Attendance Analysis
- Secure session-based role login (Teacher / Student)
- Google Sheets database integration

## Setup Guide

### 1. How to create Google Sheet
Create a new Google Sheet and add the following 5 sheet tabs with exact names:
- `students`
- `attendance`
- `videos`
- `subjects`
- `announcements`

### 2. How to enable Sheets API
Go to Google Cloud Console, create a project, and enable the "Google Sheets API" and "Google Drive API".

### 3. Where to place JSON key
Create a Service Account, generate a JSON key, and save it in the root folder as `CREDENTIALS.JSON`.
Ensure you share the Google Sheet with the `client_email` found in the JSON file.

### 4. Where to place OpenAI API Key
Create a `.env` file in the root folder and add your OpenAI API key:
`OPENAI_API_KEY=your_key_here`
`SECRET_KEY=your_flask_secret_key`

### 5. How to run Flask locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `gunicorn app:app --bind 127.0.0.1:5000` or `python app.py`

### 6. How to deploy on Render
1. Push this repository to GitHub.
2. Create a new "Web Service" on Render and connect the repo.
3. Use the start command: `gunicorn app:app`
4. In Render's Environment Variables, add `OPENAI_API_KEY` and your `SECRET_KEY`.
