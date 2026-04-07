import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace schema references with V3 to reset the gamification and progress boards
old_schema = """        'quiz_scores': ['quiz_id', 'student_id', 'student_name', 'score', 'percentage', 'timestamp'],
        'materials': ['id', 'title', 'subject', 'description', 'drive_link'],
        'schedule': ['id', 'date', 'subject', 'start_time', 'end_time', 'note'],
        'student_profiles': ['student_id', 'extra_notes', 'last_active_date'],
        'video_completion': ['date', 'student_id', 'subject', 'completed'],
        'gamification': ['student_id', 'points', 'badges'],
        'leaderboard_cache': ['student_id', 'points', 'rank'],
        'ATTENDANCE_V2': ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated'],
        'DPP_V2': ['id', 'title', 'subject', 'class', 'description', 'file_url', 'date_uploaded'],
        'DPP_Status': ['dpp_id', 'student_id', 'status'],
        'TASKS_V2': ['id', 'title', 'description', 'subject', 'class', 'due_date', 'created_date'],
        'Task_Status': ['task_id', 'student_id', 'status'],
        'Student_Metrics': ['student_id', 'xp', 'level', 'streak_days', 'last_active_date', 'reputation_score', 'trusted_devices']"""

new_schema = """        'quiz_scores_V3': ['quiz_id', 'student_id', 'student_name', 'score', 'percentage', 'timestamp'],
        'materials': ['id', 'title', 'subject', 'description', 'drive_link'],
        'schedule': ['id', 'date', 'subject', 'start_time', 'end_time', 'note'],
        'student_profiles': ['student_id', 'extra_notes', 'last_active_date'],
        'video_completion_V3': ['date', 'student_id', 'subject', 'video_id', 'completed'],
        'gamification_V3': ['student_id', 'points', 'badges'],
        'leaderboard_cache_V3': ['student_id', 'points', 'rank'],
        'ATTENDANCE_V2': ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated'],
        'DPP_V2': ['id', 'title', 'subject', 'class', 'description', 'file_url', 'date_uploaded'],
        'DPP_Status_V3': ['dpp_id', 'student_id', 'status'],
        'TASKS_V2': ['id', 'title', 'description', 'subject', 'class', 'due_date', 'created_date'],
        'Task_Status_V3': ['task_id', 'student_id', 'status'],
        'Student_Metrics_V3': ['student_id', 'xp', 'level', 'streak_days', 'last_active_date', 'reputation_score', 'trusted_devices']"""

content = content.replace(old_schema, new_schema)

# Global replaces in the file for these tables:
content = content.replace("'quiz_scores'", "'quiz_scores_V3'")
content = content.replace("'video_completion'", "'video_completion_V3'")
content = content.replace("'gamification'", "'gamification_V3'")
content = content.replace("'leaderboard_cache'", "'leaderboard_cache_V3'")
content = content.replace("'DPP_Status'", "'DPP_Status_V3'")
content = content.replace("'Task_Status'", "'Task_Status_V3'")
content = content.replace("'Student_Metrics'", "'Student_Metrics_V3'")

with open('app.py', 'w') as f:
    f.write(content)
