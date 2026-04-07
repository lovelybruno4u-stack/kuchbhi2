# ASWATHAMA CLASSES - AI-Powered Web Platform

A complete AI-powered web platform for coaching classes with role-based access, attendance management, video sharing, and AI tools for both teachers and students.

## Setup Guide

### 1. How to create Google Sheet
1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new Blank Spreadsheet.
3. Rename it to "ASWATHAMA_DB" (or any name you prefer).
4. Create the following sheets (tabs) with the exact headers in the first row:
   - **students**: `id`, `name`, `class`, `roll`, `phone`, `email`, `parent`
   - **attendance**: `date`, `student_id`, `status`
   - **videos**: `date`, `subject`, `drive_link`
   - **subjects**: `subject_name`
   - **announcements**: `date`, `message`

### 2. How to enable Sheets API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project.
3. Go to **APIs & Services > Library**.
4. Search for "Google Sheets API" and click **Enable**.
5. Search for "Google Drive API" and click **Enable**.
6. Go to **APIs & Services > Credentials**.
7. Click **Create Credentials** > **Service Account**.
8. Fill in the details and click **Create and Continue**.
9. Grant the service account the "Editor" role (optional but recommended).
10. Click on the created service account, go to the **Keys** tab.
11. Click **Add Key** > **Create new key** > **JSON**. This will download your credential file.
12. **Important**: Open your Google Sheet, click **Share**, and share it with the email address of the service account you just created (e.g., `your-service-account@your-project.iam.gserviceaccount.com`) as an **Editor**.

### 3. Where to place JSON key
1. Take the downloaded JSON file.
2. Rename it to `CREDENTIALS.JSON`.
3. Place it in the root directory of this project (same level as `app.py`).

### 4. Where to place OpenAI API key
1. Create a `.env` file in the root directory of this project (you can copy `.env.example` to `.env`).
2. Add your OpenAI API key to the `.env` file like this:
   `OPENAI_API_KEY=your_openai_api_key_here`
3. Also set `FLASK_SECRET_KEY` in the `.env` file to a random string for secure sessions.

### 5. How to run Flask locally
1. Install Python 3.8 or higher.
2. Open a terminal in the project directory.
3. (Optional) Create a virtual environment:
   `python -m venv venv`
   `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
4. Install dependencies:
   `pip install -r requirements.txt`
5. Run the application:
   `flask run` or `python app.py`
6. Open your browser and go to `http://127.0.0.1:5000/`.

### 6. How to deploy on Render
1. Create an account on [Render](https://render.com/).
2. Create a new **Web Service**.
3. Connect your GitHub repository containing this project.
4. Set the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Go to the **Environment** tab and add the following Environment Variables:
   - `OPENAI_API_KEY`: Your OpenAI API key.
   - `FLASK_SECRET_KEY`: A secure random string.
6. Since Render doesn't allow uploading files directly for free tier easily, you might need to handle the `CREDENTIALS.JSON`. You can either:
   - Base64 encode the JSON contents and store it as an environment variable (e.g., `GOOGLE_CREDENTIALS`), then modify `db.py` to decode it.
   - Or just upload `CREDENTIALS.JSON` to your private GitHub repository (Not recommended for public repos).
7. Click **Create Web Service** and wait for the deployment to finish.
