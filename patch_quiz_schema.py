import re

with open('app.py', 'r') as f:
    content = f.read()

# Make sure we got it right
content = content.replace(
    "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer'],",
    "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time'],"
)

# And if already updated:
# (Should be safe, let's verify if the original text is still there)

with open('app.py', 'w') as f:
    f.write(content)
