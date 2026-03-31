import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Fix student dashboard
# The old code had:
#     total = len(attendance) if attendance else 1
#     present = len([a for a in attendance if a['status'] == 'Present'])
#     rate = (present / total) * 100 if total > 0 else 0

regex_student = re.compile(
    r"@app\.route\('/student/dashboard', endpoint='student_dashboard'\)\n"
    r"@login_required\(role='student'\)\n"
    r"def student_dashboard\(\):\n.*?"
    r"return render_template\('student/student_dashboard\.html', stats=stats, recent_announcements=recent_announcements\)",
    re.DOTALL
)

fixed_student = """@app.route('/student/dashboard', endpoint='student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')
    subjects = get_data('subjects')

    # Safely fetch attendance and calculate rate
    attendance_data = get_data('attendance')
    if attendance_data:
        attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]
    else:
        attendance = []

    total = len(attendance) if attendance else 1
    present = len([a for a in attendance if a.get('status') == 'Present'])
    attendance_percentage = round((present / total) * 100) if len(attendance) > 0 else 0

    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')

    today_video = None
    if videos:
        for v in videos[::-1]:
            if v.get('date') == current_date:
                today_video = v
                break

    latest_announcement = announcements[-1] if announcements else None

    data = {
        'attendance_percentage': attendance_percentage,
        'today_video': today_video,
        'latest_announcement': latest_announcement,
        'subjects': subjects
    }

    return render_template('student/student_dashboard.html', data=data)"""

content = re.sub(regex_student, fixed_student, content)

with open('app.py', 'w') as f:
    f.write(content)
