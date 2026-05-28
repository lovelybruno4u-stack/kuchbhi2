# ASWATHAMA CLASSES - EdTech Platform

An AI-powered web platform for ASWATHAMA CLASSES built using Flask, Google Sheets API, and OpenAI's ChatGPT API.

## Setup Guide

### 1. How to create a Google Sheet
Create a new Google Sheet and create the following sheets EXACTLY with these names and headers in row 1:
- **students**: `id`, `name`, `class`, `roll`, `phone`, `email`, `parent`
- **attendance**: `date`, `student_id`, `status`
- **videos**: `date`, `subject`, `drive_link`
- **subjects**: `subject_name`
- **announcements**: `date`, `message`

### 2. How to enable Sheets API
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- Navigate to "APIs & Services" > "Library".
- Search for "Google Sheets API" and enable it.
- Go to "Credentials" > "Create Credentials" > "Service Account".
- Create a service account, navigate to "Keys", and create a new JSON key. This will download a JSON file.
- Open your Google Sheet, click "Share", and add the `client_email` found in your service account JSON file as an Editor.

### 3. Where to place the JSON key
Rename the downloaded JSON key file to `CREDENTIALS.JSON` and place it in the root directory of this project. (Do NOT commit this file to public repositories).

### 4. Where to place the OpenAI API key
Create a file named `.env` in the root directory of the project and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
FLASK_SECRET_KEY=your_secure_random_secret_key
```

### 5. How to run Flask locally
1. Ensure you have Python installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python app.py
   # or with Gunicorn:
   # gunicorn app:app --bind 127.0.0.1:5000
   ```
4. Access the app at `http://127.0.0.1:5000`.

### 6. How to deploy on Render
1. Push your code to a GitHub repository (do NOT push `CREDENTIALS.JSON` or `.env`).
2. Go to [Render](https://render.com/) and create a new "Web Service".
3. Connect your GitHub repository.
4. Set the Environment to "Python".
5. Set the Build Command to `pip install -r requirements.txt`.
6. Set the Start Command to `gunicorn app:app`.
7. Under "Environment Variables", add:
   - `OPENAI_API_KEY`: your OpenAI API key
   - `FLASK_SECRET_KEY`: a secure random string
   - Since you can't easily upload `CREDENTIALS.JSON` as a file on Render free tier natively without custom steps, you might need to use an environment variable containing the base64 encoded JSON, or use a secure file upload. Render's "Secret Files" feature is perfect for `CREDENTIALS.JSON`. Create a Secret File named `CREDENTIALS.JSON` and paste the raw JSON contents inside.
8. Click "Create Web Service".
