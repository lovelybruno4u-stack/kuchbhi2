# Setup Guide for ASWATHAMA CLASSES

## 1. How to create Google Sheet
The application will automatically create a Google Sheet Database for you when it first starts, including all the necessary tabs ('students', 'attendance', 'videos', 'subjects', 'announcements'). You only need to provide your `ADMIN_EMAIL` in the environment variables so the application can share it with your email address granting you edit access.

## 2. How to enable Sheets API
1. Go to Google Cloud Console (https://console.cloud.google.com/).
2. Create a new project.
3. Go to "APIs & Services" > "Library".
4. Search for "Google Sheets API" and enable it.
5. Search for "Google Drive API" and enable it as well.
6. Go to "APIs & Services" > "Credentials".
7. Click "Create Credentials" > "Service Account". Fill in the details and click create.
8. Click on the created service account > "Keys" tab > "Add Key" > "Create new key" (JSON).
9. This will download a `.json` file to your computer.
10. **Important**: Open your Service Account details, copy the email address provided. Go back to your Google Sheet, click "Share" in the top right, and share the sheet as an "Editor" with that service account email.

## 3. Where to place JSON key
Rename the downloaded `.json` file from step 2 to `credentials.json` and place it in the root folder of this project (next to `app.py`).

## 4. Where to place OpenAI API key
1. Go to OpenAI Platform (https://platform.openai.com/).
2. Generate an API Key.
3. Open the `.env` file in the root directory (create it if it doesn't exist) and add:
   ```
   OPENAI_API_KEY=your_openai_key_here
   SPREADSHEET_ID=your_spreadsheet_id
   SECRET_KEY=your_random_flask_secret_key
   ```

## 5. How to run Flask locally
1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application using Gunicorn for a local test:
   ```bash
   gunicorn app:app --bind 127.0.0.1:5000
   ```
   Or alternatively, just run `python app.py`.
4. Open your browser and go to `http://127.0.0.1:5000`.

## 6. How to deploy on Render
1. Push this codebase to a GitHub repository.
2. Go to Render.com and sign in.
3. Click "New" > "Web Service".
4. Connect your GitHub repository.
5. Use the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. Under "Advanced" -> "Environment Variables", add:
   - `OPENAI_API_KEY`
   - `SPREADSHEET_ID`
   - `SECRET_KEY`
7. For the `credentials.json`, upload it securely as a "Secret File" in Render, OR base64 encode it and set it as an env variable to decode at runtime.
8. Click "Create Web Service".
