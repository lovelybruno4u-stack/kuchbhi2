# Ashwathama Classes

A complete AI-powered web platform for educational coaching classes. Features role-based access for Teachers and Students, integrated with Google Sheets as a database, and powered by OpenAI for various educational AI tools.

## Tech Stack
* **Backend:** Flask (Python)
* **Database:** Google Sheets API (via `gspread` & Service Accounts)
* **AI:** OpenAI ChatGPT API (`gpt-4o-mini`)
* **Frontend:** HTML, CSS, JS (Glassmorphism, Responsive SaaS UI)

## Features
**Teacher (Admin)**
* Dashboard Analytics
* Student Management (CRUD)
* Attendance Tracking
* Video Library Management
* Announcements System
* AI Tools: Quiz Generator, Attendance Analyzer, Video Summarizer

**Student (User)**
* Personal Dashboard
* View Attendance & Announcements
* Watch Class Recordings
* AI Doubt Solver
* AI Study Chatbot

---

## Setup Guide

### 1. Automatic Google Sheet Creation
The application will automatically create a Google Sheet Database for you when it first starts!
It will create all the required tabs and share it to your email address. You just need to provide your `ADMIN_EMAIL` in the environment variables so you get edit access.

### 2. How to Enable Sheets API & Get Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Go to "APIs & Services" > "Library". Search for **Google Sheets API** and enable it.
4. Search for **Google Drive API** and enable it as well.
5. Go to "APIs & Services" > "Credentials".
6. Click "Create Credentials" > "Service Account". Fill in details and create.
7. Click on the created service account > "Keys" tab > "Add Key" > "Create new key" (JSON).
8. This will download a `.json` file to your computer.
9. **Important:** Open your Service Account details, copy the email address provided. Go back to your Google Sheet, click "Share" in the top right, and share the sheet as an "Editor" with that service account email.

### 3. Where to place JSON Key
Rename the downloaded file to `credentials.json` and place it in the root folder of this project (next to `app.py`).

### 4. Where to place OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/).
2. Generate an API Key.
3. Open the `.env` file in the root directory (create it if it doesn't exist) and add:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   SPREADSHEET_ID=your_spreadsheet_id_from_step_1
   SECRET_KEY=your_random_flask_secret_key
   ```

### 5. How to run Flask locally
1. Ensure Python 3.8+ is installed.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Visit `http://127.0.0.1:5000` in your browser.

### 6. How to Deploy on Render
1. Push this code to a GitHub repository. (Make sure `credentials.json` and `.env` are listed in `.gitignore` if making public! For private repo, Render provides secrets management).
2. Go to [Render.com](https://render.com) and sign in.
3. Click "New" > "Web Service".
4. Connect your GitHub repository.
5. Use the following settings:
   * **Environment:** Python
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
6. Go to "Advanced" -> "Environment Variables" and add:
   * `OPENAI_API_KEY`
   * `SPREADSHEET_ID`
   * `SECRET_KEY`
7. For the `credentials.json`, either upload it securely as a "Secret File" in Render, OR base64 encode it and set it as an env variable to decode at runtime.
8. Click "Create Web Service".
