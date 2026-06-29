# Aswathama Classes - Setup Guide

## 1. How to create a Google Sheet
Create a new Google Sheet. You will need 5 sheets with the following names and headers:
- `students`: id, name, class, roll, phone, email, parent
- `attendance`: date, student_id, status
- `videos`: date, subject, drive_link
- `subjects`: subject_name
- `announcements`: date, message

## 2. How to enable Sheets API
- Go to Google Cloud Console (https://console.cloud.google.com/).
- Create a new project.
- Navigate to "APIs & Services" > "Library".
- Search for "Google Sheets API" and enable it.
- Search for "Google Drive API" and enable it.
- Navigate to "APIs & Services" > "Credentials".
- Create credentials > Service account.
- Once created, go to the Keys tab, click Add Key > Create new key (JSON).
- Share the Google Sheet created in step 1 with the service account email generated.

## 3. Where to place JSON key
- Copy the contents of the downloaded JSON key.
- Save it in the project root folder as `CREDENTIALS.JSON`.

## 4. Where to place OpenAI API key
- Create an account on OpenAI and generate an API key.
- Create a `.env` file in the project root folder.
- Add your key: `OPENAI_API_KEY=your_api_key_here`.

## 5. How to run Flask locally
- Ensure Python is installed.
- Install requirements: `pip install -r requirements.txt`
- Run the server: `python app.py` (or `gunicorn app:app --bind 127.0.0.1:5000`)
- The app will run on `http://127.0.0.1:5000`

## 6. How to deploy on Render
- Push this code to a GitHub repository.
- Go to Render (https://render.com/) and click "New Web Service".
- Connect your GitHub repository.
- Use `pip install -r requirements.txt` as the Build Command.
- Use `gunicorn app:app` as the Start Command.
- Add Environment Variables:
  - `OPENAI_API_KEY`: your OpenAI API key
  - `GOOGLE_CREDENTIALS`: contents of your `CREDENTIALS.JSON` (you will need to modify the code to load from env var or manage secret files).
