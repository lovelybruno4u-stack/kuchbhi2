# ASWATHAMA CLASSES

A complete AI-powered web platform for edtech, built with Flask, Google Sheets API, and ChatGPT.

## Setup Instructions

### 1. How to create a Google Sheet
1. Go to [Google Sheets](https://sheets.google.com).
2. Create a new blank spreadsheet.
3. Rename it to something like `Aswathama Classes Database`.
4. Create the following exact tabs (sheets) at the bottom:
   - `students`
   - `attendance`
   - `videos`
   - `subjects`
   - `announcements`
5. Note the Spreadsheet ID from the URL (e.g., `https://docs.google.com/spreadsheets/d/<THIS_IS_THE_ID>/edit`). You will need this for the `.env` file.

### 2. How to enable Google Sheets API & Get Credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project.
3. In the search bar, look for "Google Sheets API" and click **Enable**.
4. Also search for "Google Drive API" and click **Enable**.
5. Go to **APIs & Services** > **Credentials**.
6. Click **Create Credentials** > **Service Account**.
7. Name it and click **Create and Continue**, then **Done**.
8. Click on the created service account, go to the **Keys** tab.
9. Click **Add Key** > **Create new key** > Choose **JSON**. This will download a `.json` file to your computer.
10. **CRITICAL:** Open your Google Sheet, click **Share** in the top right, and share it with the `client_email` address found inside the downloaded JSON file. Give it **Editor** access.

### 3. Where to place the JSON key
1. Open the `.json` file you downloaded.
2. Copy all of its contents.
3. Paste the contents into the `CREDENTIALS.JSON` file in the root of this project folder.

### 4. Where to place the OpenAI API Key and other Configs
Create a file named `.env` in the root of the project and add the following lines:
```env
# Required: Your OpenAI API key for AI features
OPENAI_API_KEY=your_openai_api_key_here

# Required: The Google Sheet ID from step 1
GOOGLE_SHEET_ID=your_spreadsheet_id_here

# Optional: A secret key for Flask sessions (can be any random string)
FLASK_SECRET_KEY=super_secret_session_key
```

### 5. How to run Flask locally
1. Ensure Python 3 is installed.
2. Open a terminal in the project directory.
3. (Optional but recommended) Create a virtual environment: `python3 -m venv venv` and activate it (`source venv/bin/activate` or `venv\Scripts\activate` on Windows).
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python3 app.py` (or `flask run`)
6. Open your browser and go to `http://127.0.0.1:5000/`.
   *Note: If Google Sheets credentials are not set up or fail, the app runs in a local "Fallback/Mock DB" mode for testing.*

### 6. How to deploy on Render
1. Create a GitHub repository and push your code (make sure NOT to push the real `CREDENTIALS.JSON` or `.env` if it's public. Render allows you to add secrets directly).
2. Go to [Render.com](https://render.com) and create an account.
3. Click **New** > **Web Service**.
4. Connect your GitHub repository.
5. Setup the deployment:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Go to **Environment Variables** in Render and add:
   - `OPENAI_API_KEY`
   - `GOOGLE_SHEET_ID`
   - `FLASK_SECRET_KEY`
7. For the `CREDENTIALS.JSON`, Render supports "Secret Files". Add a secret file named `CREDENTIALS.JSON` and paste your service account JSON contents there.
8. Click **Deploy Web Service**.