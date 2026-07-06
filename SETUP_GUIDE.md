# Setup Guide for ASWATHAMA CLASSES

## 1. How to create Google Sheet
1. Go to Google Sheets and create a new blank spreadsheet.
2. The application will automatically create the required sheets (like `students`, `attendance`, `videos`, `subjects`, `announcements`) with their schemas upon first run if they don't exist.
3. Note the long string of characters in the URL (this is your `SPREADSHEET_ID`).

## 2. How to enable Sheets API
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Go to "APIs & Services" > "Library" and enable the **Google Sheets API**.
4. Enable the **Google Drive API** as well.
5. Go to "Credentials" > "Create Credentials" > "Service Account".
6. Complete the setup and generate a new JSON key.
7. Important: Copy the Service Account's email address and share your Google Sheet with this email (Editor access).

## 3. Where to place JSON key
Rename the downloaded JSON key file to `CREDENTIALS.JSON` (or `credentials.json`) and place it in the root folder of this project (next to `app.py`).

## 4. Where to place OpenAI API key
1. Get an API key from [OpenAI](https://platform.openai.com/).
2. Create a `.env` file in the root directory.
3. Add the following lines:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SPREADSHEET_ID=your_google_spreadsheet_id_here
   SECRET_KEY=your_flask_secret_key_here
   ```

## 5. How to run Flask
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   python app.py
   ```
3. Visit `http://127.0.0.1:5000` in your browser.

## 6. How to deploy on Render
1. Push this project to GitHub (ensure `CREDENTIALS.JSON` and `.env` are listed in `.gitignore` if it's a public repository).
2. Go to [Render](https://render.com) and create a new Web Service linked to your GitHub repo.
3. Set the Environment to Python.
4. Set the Build Command to `pip install -r requirements.txt`.
5. Set the Start Command to `gunicorn app:app --bind 0.0.0.0:$PORT`.
6. Add the Environment Variables (`OPENAI_API_KEY`, `SPREADSHEET_ID`, `SECRET_KEY`) under Render's Advanced settings.
7. For the service account, you can either upload it as a Secret File named `credentials.json` or pass the raw JSON string in an environment variable `GOOGLE_CREDENTIALS`.
