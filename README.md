# ASWATHAMA CLASSES

## Setup Guide

1. **How to create Google Sheet**
   - Go to Google Sheets (sheets.new) and create a new spreadsheet.
   - Name it "Aswathama Classes Database" or similar.
   - Note the long ID in the URL, this is your `SPREADSHEET_ID`.

2. **How to enable Sheets API**
   - Go to Google Cloud Console (console.cloud.google.com).
   - Create a new project.
   - Go to "APIs & Services" > "Library" and search for "Google Sheets API", then enable it.

3. **Where to place JSON key**
   - In your Google Cloud Project, go to "APIs & Services" > "Credentials".
   - Click "Create Credentials" > "Service Account".
   - Fill in details, then create and download the JSON key.
   - Place this file in the root directory of this project and rename it to `credentials.json`.
   - *Important:* Open the JSON file, find the `client_email`, and share your Google Sheet with this email address as an Editor.

4. **Where to place OpenAI API key**
   - Create a `.env` file in the root directory.
   - Add the following line: `OPENAI_API_KEY=your_openai_api_key_here`

5. **How to run Flask**
   - Create a virtual environment: `python -m venv venv`
   - Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
   - Install requirements: `pip install -r requirements.txt`
   - Run the app: `gunicorn app:app --bind 127.0.0.1:5000` or `python app.py`

6. **How to deploy on Render**
   - Create a new Web Service on Render (render.com) and connect your GitHub repo.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - In Environment Variables, set:
     - `OPENAI_API_KEY` to your OpenAI key.
     - `SPREADSHEET_ID` to your Google Sheet ID.
     - `GOOGLE_CREDENTIALS` to the raw JSON string of your `credentials.json` (optional, if you don't commit it).
