import re

with open('app.py', 'r') as f:
    content = f.read()

# Update schema
content = content.replace(
    "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer'],",
    "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time'],"
)

# Replace teacher_quiz to handle grouping by date/subject possibly?
# Let's check how teacher/quiz.html displays things later.

with open('app.py', 'w') as f:
    f.write(content)
