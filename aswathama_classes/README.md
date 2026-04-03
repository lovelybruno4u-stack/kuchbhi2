# ASWATHAMA CLASSES

ASWATHAMA CLASSES is a complete AI-powered web platform for coaching classes. It is built using a Python/Flask backend and HTML/CSS/JS frontend, utilizing Google Sheets as its database and integrating OpenAI's ChatGPT API for AI features.

## Roles
- **Teacher (Admin)**: Can manage students, mark attendance, add daily class videos, add subjects, post announcements, and use AI tools (announcement generation, video summary, attendance analysis, quiz generation).
- **Student (User)**: Can view dashboard, attendance, videos, announcements, and use AI study chatbot and AI doubt solver.

## Setup Guide

### 1. How to Create Google Sheet
1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new blank spreadsheet.
3. Name it "ASWATHAMA_CLASSES_DB" (or any name you prefer).
4. Create the following sheets (tabs at the bottom) with the exact headers in the first row:
    - **Sheet1: students**
        - id, name, class, roll, phone, email, parent
    - **Sheet2: attendance**
        - date, student_id, status
    - **Sheet3: videos**
        - date, subject, drive_link
    - **Sheet4: subjects**
        - subject_name
    - **Sheet5: announcements**
        - date, message

### 2. How to Enable Sheets API and Get Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Navigate to "APIs & Services" > "Library".
4. Search for "Google Sheets API" and enable it.
5. Search for "Google Drive API" and enable it.
6. Navigate to "APIs & Services" > "Credentials".
7. Click "Create Credentials" > "Service Account".
8. Fill in details and create the service account.
9. Click on the created service account, go to "Keys" > "Add Key" > "Create new key".
10. Choose JSON and download the file.
11. **Important:** Open your Google Sheet, click "Share" in the top right, and share it with the email address of the service account you just created (e.g., `your-service-account@your-project.iam.gserviceaccount.com`), giving it "Editor" access.

### 3. Where to Place JSON Key
1. Rename the downloaded JSON key file to `CREDENTIALS.JSON`.
2. Place this `CREDENTIALS.JSON` file in the root directory of the project (same folder as `app.py`).

### 4. Where to Place OpenAI API Key and other Env Variables
1. Create a `.env` file in the root directory.
2. Add your OpenAI API key and the exact name of your Google Sheet:
```
OPENAI_API_KEY=your_openai_api_key_here
SHEET_NAME=ASWATHAMA_CLASSES_DB
FLASK_SECRET_KEY=your_secure_random_secret_key_here
```

### 5. How to Run Flask Locally
1. Ensure Python 3 is installed.
2. Navigate to the project directory: `cd aswathama_classes`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python app.py`
5. Access the app in your browser at `http://127.0.0.1:5000`

### 6. How to Deploy on Render
1. Create a GitHub repository and push this code to it. (Do not push your `.env` or real `CREDENTIALS.JSON`!).
2. Go to [Render](https://render.com/) and create an account/login.
3. Click "New" > "Web Service".
4. Connect your GitHub repository.
5. In the settings:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. Under "Environment Variables" in Render, add:
   - `OPENAI_API_KEY` = your api key
   - `SHEET_NAME` = your sheet name
   - `FLASK_SECRET_KEY` = your secret key
   - Add the contents of your `CREDENTIALS.JSON` as an environment variable or secret file depending on your setup. Render allows you to add "Secret Files", you can upload your `CREDENTIALS.JSON` there and name it `CREDENTIALS.JSON`.
7. Deploy.

## AI Prompts Used
- **Doubt Solver**: "Explain this concept in very simple words for a school student"
- **Quiz Generator**: "Generate 5 MCQ questions with answers"
- **Announcement Generator**: "Write a professional coaching class announcement"
- **Attendance Insight**: "Analyze attendance data and provide insights"
- **Video Summary**: "Generate summary notes for revision"
