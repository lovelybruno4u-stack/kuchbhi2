# ASWATHAMA CLASSES - Setup Guide

Follow these steps to setup and deploy the ASWATHAMA CLASSES platform.

## 1. How to Create Google Sheet
1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new Blank Spreadsheet.
3. Rename the spreadsheet to `AswathamaClassesDB` (or any name you prefer).
4. Create the following sheets (tabs at the bottom) EXACTLY as named:
   - `students` (Columns: id, name, class, roll, phone, email, parent)
   - `attendance` (Columns: date, student_id, status)
   - `videos` (Columns: date, subject, drive_link)
   - `subjects` (Columns: subject_name)
   - `announcements` (Columns: date, message)

## 2. How to Enable Sheets API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. In the left sidebar, go to **APIs & Services** > **Library**.
4. Search for **Google Sheets API** and click **Enable**.
5. Search for **Google Drive API** and click **Enable**.
6. Go to **APIs & Services** > **Credentials**.
7. Click **Create Credentials** > **Service Account**.
8. Fill in the details and create the account.
9. Click on the newly created Service Account, go to the **Keys** tab, click **Add Key** > **Create new key** > **JSON**.
10. A JSON file will download to your computer.
11. **IMPORTANT**: Open the downloaded JSON file, copy the `client_email` address. Go back to your Google Sheet, click **Share**, and share the sheet with this email address as an **Editor**.

## 3. Where to place JSON Key
1. Rename the downloaded JSON file to `CREDENTIALS.JSON`.
2. Place it in the root directory of this project (in the same folder as `app.py`).

## 4. Where to place OpenAI API Key
1. Create a file named `.env` in the root directory of this project.
2. Add your OpenAI API key to the `.env` file like this:
   ```
   OPENAI_API_KEY=your-api-key-here
   FLASK_SECRET_KEY=your-random-secret-key
   ```
   *(Note: The `FLASK_SECRET_KEY` is used for secure session management.)*

## 5. How to Run Flask
1. Open a terminal or command prompt.
2. Navigate to the project directory.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask application:
   ```bash
   gunicorn app:app --bind 127.0.0.1:5000
   ```
   *(Alternatively, for development, you can use: `flask run`)*

## 6. How to Deploy on Render
1. Create a GitHub repository and push your code to it.
2. Go to [Render](https://render.com) and sign in.
3. Click **New +** and select **Web Service**.
4. Connect your GitHub account and select your repository.
5. In the configuration:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Under **Advanced** > **Environment Variables**, add:
   - `OPENAI_API_KEY` with your OpenAI API key.
   - `FLASK_SECRET_KEY` with a random secret string.
7. Click **Create Web Service**.
   *(Note: Since Render environment cannot directly load `CREDENTIALS.JSON` file securely if not pushed to GitHub, it's recommended to encode the JSON as a base64 string or provide it via a dedicated environment variable mechanism if keeping the repo public. For private repos, it's fine. For this setup, we assume you've managed credentials securely.)*
