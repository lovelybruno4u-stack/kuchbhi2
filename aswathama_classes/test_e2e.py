import requests
import time
import subprocess

import os

# Start server
current_env = os.environ.copy()
current_env["OPENAI_API_KEY"] = "dummy"
current_env["FLASK_SECRET_KEY"] = "dummy"

server = subprocess.Popen(["python", "app.py"], env=current_env)
time.sleep(2) # Give it a moment to boot

try:
    # Use a session to persist cookies
    session = requests.Session()

    # 1. Test redirect from root to login
    r = session.get("http://127.0.0.1:5000/")
    assert "Login" in r.text, "Should redirect and show Login page"

    # 2. Login as Teacher
    r = session.post("http://127.0.0.1:5000/login", data={"role": "teacher", "password": "admin123"})
    assert "Teacher Dashboard" in r.text, "Teacher login failed"

    # Check a teacher route
    r = session.get("http://127.0.0.1:5000/teacher/students")
    assert "Students Directory" in r.text, "Teacher students route failed"

    # Add a dummy student using Teacher privileges to test student login
    r = session.post("http://127.0.0.1:5000/teacher/students", data={
        "action": "add", "name": "Req Test Student", "class": "10", "roll": "1", "parent": "Parent"
    })

    # Fetch students to find the ID (we scrape it roughly)
    r = session.get("http://127.0.0.1:5000/teacher/students")
    # Simple regex or string search to find ID. Let's assume the mock ID is 8 chars long.
    import re
    match = re.search(r'<td style="font-family: monospace;">([a-f0-9]{8})</td>', r.text)
    if match:
        student_id = match.group(1)

        # Logout
        session.get("http://127.0.0.1:5000/logout")

        # 3. Login as Student
        r = session.post("http://127.0.0.1:5000/login", data={"role": "student", "student_id": student_id})
        assert "Student Dashboard" in r.text, "Student login failed"

        # Check a student route
        r = session.get("http://127.0.0.1:5000/student/chatbot")
        assert "Study Tutor" in r.text, "Student chatbot route failed"

    print("All End-to-End checks passed successfully.")

finally:
    server.terminate()
