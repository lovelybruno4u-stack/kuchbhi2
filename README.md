# ASWATHAMA CLASSES

A complete AI-powered web platform for edtech.

## Setup Guide

### 1. How to create a Google Sheet
1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new blank spreadsheet.
3. Add the following sheets exactly with these names and headers (Row 1):
   - **students**: `id`, `name`, `class`, `roll`, `phone`, `email`, `parent`
   - **attendance**: `date`, `student_id`, `status`
   - **videos**: `date`, `subject`, `drive_link`
   - **subjects**: `subject_name`
   - **announcements**: `date`, `message`

### 2. How to enable Sheets API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to **APIs & Services > Library**.
4. Search for "Google Drive API" and click **Enable**.
5. Search for "Google Sheets API" and click **Enable**.
6. Go to **APIs & Services > Credentials**.
7. Click **Create Credentials** and select **Service Account**.
8. Fill in the service account details and click Create.
9. Click on the newly created service account, go to the **Keys** tab.
10. Click **Add Key > Create New Key** and choose **JSON**. This will download the JSON key file.
11. **Crucial:** Open your Google Sheet, click **Share**, and share the sheet as an Editor with the `client_email` found inside your downloaded JSON key file.

### 3. Where to place the JSON key
Rename the downloaded JSON file to `CREDENTIALS.JSON` and place it in the root directory of this project. (An empty placeholder file is already present, please replace its contents with your actual credentials).

### 4. Where to place OpenAI API key
1. Create a file named `.env` in the root directory of this project.
2. Add the following lines to it:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_SECRET_KEY=your_random_secret_key_here
   SPREADSHEET_ID=your_google_sheet_id_here
   ```
   *(The Google Sheet ID is the long random string in your Google Sheet's URL).*

### 5. How to run Flask locally
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
   *Alternatively, use gunicorn for testing production server:*
   ```bash
   gunicorn app:app --bind 127.0.0.1:5000
   ```
3. Open `http://127.0.0.1:5000` in your browser.

### 6. How to deploy on Render
1. Push your code to a GitHub repository.
2. Create a new account or log in to [Render](https://render.com).
3. Click **New +** and select **Web Service**.
4. Connect your GitHub repository.
5. In the settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Under **Environment Variables**, add:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_SECRET_KEY`: A strong random string
   - `SPREADSHEET_ID`: Your Google Sheet ID
   - `GOOGLE_CREDENTIALS_JSON`: The raw JSON string contents of your `CREDENTIALS.JSON` file (if you choose to use env vars instead of a file in production).
7. Click **Create Web Service**.
