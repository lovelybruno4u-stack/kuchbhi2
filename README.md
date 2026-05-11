# ASWATHAMA CLASSES

An AI-powered web platform for modern edtech coaching, built with Flask, Google Sheets, and OpenAI API.

## Setup Guide

### 1. How to create Google Sheet
Create a new Google Sheet and rename it (e.g., `Aswathama Classes Database`).
You must create exactly these 5 sheets inside it:
- `students`: id, name, class, roll, phone, email, parent
- `attendance`: date, student_id, status
- `videos`: date, subject, drive_link
- `subjects`: subject_name
- `announcements`: date, message

### 2. How to enable Sheets API
- Go to the Google Cloud Console.
- Create a new project.
- Enable the Google Sheets API and Google Drive API.
- Create Credentials > Service Account.
- Generate a JSON key for the Service Account.
- **IMPORTANT**: Share your Google Sheet with the email address of the service account as an Editor.

### 3. Where to place JSON key
Place the downloaded JSON key file in the root of the project and rename it to `CREDENTIALS.JSON`.

### 4. Where to place OpenAI API key
Create a `.env` file in the root of the project (copy from `.env.example`).
Add your OpenAI API key:
`OPENAI_API_KEY=your_openai_api_key_here`

### 5. How to run Flask locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
   Or use Flask run:
   ```bash
   flask run
   ```

### 6. How to deploy on Render
- Push your code to GitHub.
- Create a new Web Service on Render and connect your GitHub repository.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Add Environment Variables in the Render dashboard:
  - `OPENAI_API_KEY`
  - For Google Sheets credentials, you can either inject `CREDENTIALS.JSON` as a secret file, or convert the JSON to a base64 string and store it as an environment variable (you would need to modify `app.py` slightly to parse it). Alternatively, since Render supports Secret Files, create a secret file named `CREDENTIALS.JSON` and paste the contents of your key.
