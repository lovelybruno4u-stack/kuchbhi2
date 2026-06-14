# ASWATHAMA CLASSES

ASWATHAMA CLASSES is a complete AI-powered web platform built for modern coaching classes. It provides a secure, role-based session system with dedicated interfaces for Teachers (Admins) and Students (Users).

## Features
- **Modern SaaS UI**: Built with a sleek glassmorphism design, responsive layouts, sidebar navigation, and smooth animations.
- **Role-based Authentication**: Secure teacher and student login systems with distinct dashboards.
- **Teacher Dashboard**: Manage students, take daily attendance, schedule daily class videos, manage subjects, and post announcements.
- **Student Dashboard**: View enrolled class videos, track attendance statistics, and view class announcements.
- **AI Tools Integration** (Powered by ChatGPT API):
    - **AI Doubt Solver**: Simplifies complex concepts into student-friendly language. Gives step-by-step math solutions.
    - **AI Study Chatbot**: A friendly virtual tutor integrated into the student dashboard.
    - **AI Attendance Analysis**: Analyzes attendance records to give teachers insights on irregular students and actionable advice.
    - **AI Video Summary**: Generates revision notes based on a class video's topic.
    - **AI Quiz Generator**: Generates 5 quick MCQs to test a topic.
    - **AI Smart Announcements**: Drafts professional announcements on behalf of the teacher.
- **Database**: Integrated with Google Sheets API as the primary database source.

## Setup Guide

### 1. How to create a Google Sheet
- Go to [Google Sheets](https://docs.google.com/spreadsheets).
- Create a new blank spreadsheet.
- Create 5 separate sheets at the bottom and name them exactly: `students`, `attendance`, `videos`, `subjects`, and `announcements`.
- For `students`, set headers: `id`, `name`, `class`, `roll`, `phone`, `email`, `parent`.
- For `attendance`, set headers: `student_id`, `student_name`, `class`, `date`, `status`, `last_updated`.
- For `videos`, set headers: `date`, `subject`, `drive_link`.
- For `subjects`, set headers: `subject_name`.
- For `announcements`, set headers: `date`, `message`.

### 2. How to enable Sheets API
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Search for "Google Sheets API" in the API Library and click "Enable".
- Search for "Google Drive API" and click "Enable".
- Go to "Credentials", click "Create Credentials", and select "Service Account".
- Once created, go to the "Keys" tab for the service account, click "Add Key" -> "Create new key", and choose JSON. This will download a JSON file.
- Finally, copy the email address of the service account and share your Google Sheet with this email address, granting it "Editor" access.

### 3. Where to place the JSON key
- Rename the downloaded JSON file to `CREDENTIALS.JSON`.
- Place this file in the root directory of the project (same level as `app.py`).

### 4. Where to place the OpenAI API key
- Create a file named `.env` in the root directory of the project.
- Add your key to the file like this:
  `OPENAI_API_KEY=your_actual_openai_api_key_here`
- You can also add `SECRET_KEY=your_flask_secret_key` for session security and `GOOGLE_SHEET_NAME=your_sheet_name` to define the target Google Sheet.

### 5. How to run Flask locally
- Ensure Python 3 is installed.
- Open a terminal and run `pip install -r requirements.txt`.
- Run the application using the command `python3 app.py` or use gunicorn with `gunicorn app:app --bind 127.0.0.1:5000`.
- Visit `http://127.0.0.1:5000` in your web browser.

### 6. How to deploy on Render
- Push this code to a GitHub repository.
- Go to [Render](https://render.com/), sign in, and click "New" -> "Web Service".
- Connect your GitHub repository.
- Use `pip install -r requirements.txt` as the Build Command.
- Use `gunicorn app:app` as the Start Command.
- In the "Environment" tab on Render, add your environment variables (`OPENAI_API_KEY`, `SECRET_KEY`, `GOOGLE_SHEET_NAME`) and you can paste the contents of your `CREDENTIALS.JSON` into an environment variable as well if you adapt the codebase to read credentials from env vars.
