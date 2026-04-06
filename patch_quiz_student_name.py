import re

with open('app.py', 'r') as f:
    content = f.read()

# Fix 1: Make sure submit_quiz uses user_name
content = content.replace("student_name = session.get('name', 'Student')", "student_name = session.get('user_name', 'Student')")

with open('app.py', 'w') as f:
    f.write(content)
