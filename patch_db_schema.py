import re

with open('app.py', 'r') as f:
    content = f.read()

# Add Student_Metrics to sheets schema
old_schema = """        'Task_Status': ['task_id', 'student_id', 'status']
    }"""

new_schema = """        'Task_Status': ['task_id', 'student_id', 'status'],
        'Student_Metrics': ['student_id', 'xp', 'level', 'streak_days', 'last_active_date', 'reputation_score', 'trusted_devices']
    }"""

if old_schema in content:
    content = content.replace(old_schema, new_schema)
    print("Patched schema")
else:
    print("Schema patch failed")

with open('app.py', 'w') as f:
    f.write(content)
