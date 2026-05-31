# ASWATHAMA CLASSES

A COMPLETE AI-powered web platform for an edtech coaching class.

## Setup Guide

Follow these steps to set up and run the platform:

### 1. How to create a Google Sheet
- Go to [Google Sheets](https://sheets.google.com/) and create a new blank spreadsheet.
- At the bottom, rename "Sheet1" and add new sheets so you have exactly these sheet names (case sensitive):
  1. `students` (Columns: id, name, class, roll, phone, email, parent)
  2. `attendance` (Columns: date, student_id, status)
  3. `videos` (Columns: date, subject, drive_link)
  4. `subjects` (Columns: subject_name)
  5. `announcements` (Columns: date, message)

### 2. How to enable Sheets API
- Go to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project.
- In the sidebar, navigate to **APIs & Services > Library**.
- Search for **Google Sheets API** and click "Enable".
- Search for **Google Drive API** and click "Enable".
- Go to **APIs & Services > Credentials**.
- Click **Create Credentials** and select **Service Account**.
- Follow the prompts to create it.
- Click on the created Service Account, go to the **Keys** tab, click **Add Key > Create New Key**, and choose **JSON**.
- The JSON file will download to your computer.

### 3. Where to place the JSON key
- Open the downloaded JSON file, copy its entire contents.
- In the root of this project, there is an empty file named `CREDENTIALS.JSON`.
- Paste the copied JSON contents into this `CREDENTIALS.JSON` file and save it.
- **Important:** Go back to your Google Sheet, click the "Share" button in the top right, and share it with the `client_email` address found inside your `CREDENTIALS.JSON` file (give it "Editor" access).

### 4. Where to place the OpenAI API key
- Get your API key from [OpenAI](https://platform.openai.com/api-keys).
- Open the `.env` file in the root directory.
- Replace `your_openai_api_key_here` with your actual API key:
  ```env
  FLASK_SECRET_KEY=supersecretkey
  OPENAI_API_KEY=sk-your-actual-api-key-here
  ```
- Also, add your Google Sheet ID to the `.env` file to connect the database:
  ```env
  GOOGLE_SHEET_ID=your_spreadsheet_id_from_the_url
  ```

### 5. How to run Flask locally
- Ensure you have Python installed.
- Open a terminal in the project root.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Run the application:
  ```bash
  python app.py
  # OR
  gunicorn app:app --bind 127.0.0.1:5000
  ```
- Open `http://127.0.0.1:5000` in your browser.

### 6. How to deploy on Render
- Go to [Render.com](https://render.com/) and create a free account.
- Push this code repository to GitHub.
- On Render, click **New > Web Service**.
- Connect your GitHub account and select this repository.
- Use the following settings:
  - **Environment:** Python
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn app:app`
- Click **Advanced** and add Environment Variables:
  - `FLASK_SECRET_KEY` = `<your random secret>`
  - `OPENAI_API_KEY` = `<your openai api key>`
  - `GOOGLE_SHEET_ID` = `<your spreadsheet id>`
- Instead of using a local `CREDENTIALS.JSON` on Render, it is recommended to store the JSON content in an environment variable or use Render's Secret Files feature to upload the `CREDENTIALS.JSON` file directly.
- Click **Create Web Service**. Wait for the deployment to finish, and your app will be live!

## Login Details for Demo Mode
If the database connection fails or you don't configure Google Sheets, the application defaults to a "Mock DB" mode for demonstration purposes.

- **Teacher Login:** Role `teacher`, Username `admin`, Password `admin`
- **Student Login:** Role `student`, Username `student`, Password `student`
