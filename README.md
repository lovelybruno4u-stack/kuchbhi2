# ASWATHAMA CLASSES

An AI-powered web platform for an edtech startup. It features a modern SaaS UI, roles for Teachers and Students, and a Google Sheets-backed database system with integrated ChatGPT AI capabilities.

## Tech Stack
- **Backend**: Flask, gspread, Google Sheets API, OpenAI API
- **Frontend**: HTML, CSS, JS with Glassmorphism and SaaS-like design (no specific frontend framework).
- **Authentication**: Session-based, Role-based (Teacher/Student)

## Setup Guide

### 1. How to create Google Sheet
1. Go to Google Sheets and create a new spreadsheet.
2. Create 5 sheets at the bottom named exactly: `students`, `attendance`, `videos`, `subjects`, `announcements`.
3. Fill in the column headers for each sheet as follows:
   - **students**: `id`, `name`, `class`, `roll`, `phone`, `email`, `parent`
   - **attendance**: `date`, `student_id`, `status`
   - **videos**: `date`, `subject`, `drive_link`
   - **subjects**: `subject_name`
   - **announcements**: `date`, `message`

### 2. How to enable Sheets API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Search for "Google Sheets API" and "Google Drive API" in the library and enable both.
4. Go to **Credentials** -> **Create Credentials** -> **Service Account**.
5. Once created, click on the service account, go to **Keys** -> **Add Key** -> **Create New Key**, and choose JSON format. Download the file.
6. Open your Google Sheet, click **Share**, and paste the `client_email` found in your downloaded JSON file. Give it "Editor" access.

### 3. Where to place JSON key
Rename the downloaded JSON file to `CREDENTIALS.JSON` and place it in the root directory of this project (next to `app.py`).

### 4. Where to place OpenAI API key
1. Create an account on the [OpenAI Platform](https://platform.openai.com/).
2. Generate an API Key under API Keys.
3. Open the `.env` file in the root directory (or create it if it doesn't exist) and set `OPENAI_API_KEY`:
```
OPENAI_API_KEY=your_key_here
FLASK_SECRET_KEY=some_random_secret_string
```

### 5. How to run Flask
1. Install requirements: `pip install -r requirements.txt`
2. Run the application: `python app.py` (or `gunicorn app:app --bind 127.0.0.1:5000`)
3. Access the app at `http://127.0.0.1:5000`

### 6. How to deploy on Render
1. Push this repository to GitHub.
2. Go to [Render](https://render.com/) and create a new **Web Service**.
3. Connect your GitHub repository.
4. Set Build Command to: `pip install -r requirements.txt`
5. Set Start Command to: `gunicorn app:app`
6. Add the environment variables:
   - `OPENAI_API_KEY`
   - `FLASK_SECRET_KEY`
   - For `CREDENTIALS.JSON`, you can store the JSON content as an environment variable (e.g. `GOOGLE_CREDENTIALS_JSON`) and modify `app.py` to read from it, or use Render's "Secret Files" feature to upload `CREDENTIALS.JSON` securely.
