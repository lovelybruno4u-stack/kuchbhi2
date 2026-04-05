import re

with open('templates/student/quiz.html', 'r') as f:
    content = f.read()

# Replace q_{{ q.id }} with q_{{ q.id }}_{{ loop.index }}
if 'name="q_{{ q.id }}"' in content:
    content = content.replace('name="q_{{ q.id }}"', 'name="q_{{ q.id }}_{{ loop.index }}"')
    print("Fixed radio button grouping.")
else:
    print("Could not find the target string. The bug might be different.")

with open('templates/student/quiz.html', 'w') as f:
    f.write(content)
