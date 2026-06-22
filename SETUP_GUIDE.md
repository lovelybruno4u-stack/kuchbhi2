# ASWATHAMA CLASSES Setup Guide

This guide will walk you through setting up the application locally and deploying it to Render.

## 1. How to Create the Google Sheet Database

1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new blank spreadsheet.
3. Rename the spreadsheet (e.g., "Aswathama Database").
4. Create the following exact tabs (sheets) with the specified columns in the first row:
   - **students**: id, name, class, roll, phone, email, parent
   - **attendance**: student_id, student_name, class, date, status, last_updated
   - **videos**: date, subject, drive_link
   - **subjects**: subject_name
   - **announcements**: date, message
5. Share this spreadsheet with the Service Account Email you generate in the next step (give it "Editor" access).

## 2. How to Enable Google Sheets API & Get Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Aswathama EdTech").
3. Navigate to **APIs & Services > Library**.
4. Search for "Google Sheets API" and click **Enable**.
5. Search for "Google Drive API" and click **Enable**.
6. Navigate to **APIs & Services > Credentials**.
7. Click **Create Credentials** and select **Service Account**.
8. Fill in the details and create the service account.
9. Click on the created service account, go to the **Keys** tab.
10. Click **Add Key** > **Create New Key**, choose **JSON**, and download the file.
11. Note the service account email (ends with `...iam.gserviceaccount.com`) and share your Google Sheet with this email as an Editor.

## 3. Where to Place the JSON Key

1. Rename the downloaded JSON file to `CREDENTIALS.JSON`.
2. Place this file in the root directory of your project (same level as `app.py`).

## 4. Where to Place the OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys) and generate an API key.
2. In the root directory of the project, create a file named `.env`.
3. Add the following line to the `.env` file:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   FLASK_SECRET_KEY=your_random_secret_key_here
   SHEET_URL=your_google_sheet_url_here
   ```
   *(Note: The `SHEET_URL` should be the full URL of your Google Sheet).*

## 5. How to Run Flask Locally

1. Open your terminal in the project root directory.
2. It's recommended to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application using Gunicorn (or Flask):
   ```bash
   gunicorn app:app --bind 127.0.0.1:5000
   ```
   *Alternatively for development: `flask run`*
5. Open your browser and go to `http://127.0.0.1:5000`.

## 6. How to Deploy on Render

1. Create an account on [Render](https://render.com/).
2. Click **New** > **Web Service**.
3. Connect your GitHub repository containing this project.
4. Set the following details:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. In the Render dashboard for your service, go to **Environment** > **Environment Variables** and add:
   - `OPENAI_API_KEY`: your OpenAI key.
   - `FLASK_SECRET_KEY`: a random string.
   - `SHEET_URL`: the URL to your Google Sheet.
6. **Handling the Credentials File on Render:**
   - Render does not allow uploading physical files directly via the dashboard.
   - You have two options:
     1. Base64 encode the contents of your `CREDENTIALS.JSON` and store it as an environment variable (e.g., `GOOGLE_CREDENTIALS_B64`), then modify `app.py` to decode it at runtime.
     2. (As currently implemented for simplicity) Include `CREDENTIALS.JSON` in your private GitHub repository so Render clones it. *Do not make the repo public if doing this.*
7. Click **Deploy** and wait for the build to finish.
