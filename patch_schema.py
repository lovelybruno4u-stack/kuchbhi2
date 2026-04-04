import re

with open('app.py', 'r') as f:
    content = f.read()

# Add quiz_scores to schema
if "'quiz_scores':" not in content:
    content = content.replace(
        "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time'],",
        "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time'],\n        'quiz_scores': ['quiz_id', 'student_id', 'student_name', 'score', 'percentage', 'timestamp'],"
    )

with open('app.py', 'w') as f:
    f.write(content)
