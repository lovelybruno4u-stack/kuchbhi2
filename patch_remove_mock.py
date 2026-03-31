with open('app.py', 'r') as f:
    content = f.read()

import re

# Remove MOCK DATA dictionary completely
mock_data_regex = re.compile(r'# MOCK DATA FOR DEVELOPMENT WITHOUT ACTIVE GOOGLE SHEET\n.*?}\n', re.DOTALL)
content = re.sub(mock_data_regex, '', content)

# Change get_data to return empty list instead of mock fallback
new_get_data = """
def get_data(sheet_name):
    sheet = get_google_sheet(sheet_name)
    if sheet:
        try:
            return sheet.get_all_records()
        except Exception as e:
            print(f"Error reading records from {sheet_name}: {e}")
            return []
    else:
        print(f"Failed to access Google Sheet '{sheet_name}'. Ensure tab exists and permissions are granted.")
        return []
"""

old_get_data_regex = re.compile(r'def get_data\(sheet_name\):.*?return mock_db\.get\(sheet_name, \[\]\)', re.DOTALL)
content = re.sub(old_get_data_regex, new_get_data.strip(), content)

# Remove mock_db appends from all POST routes
# We just need to remove lines containing `mock_db['`
lines = content.split('\n')
new_lines = []
for line in lines:
    if "mock_db['" not in line:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Fix student login since mock_db is gone
# we need to ensure the attendance route doesn't crash on mock_db too
# Just clean up attendance save
old_att = """@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('attendance')
    if sheet:
        rows_to_insert = []
        for record in records:
            # Update local mock db for immediate testing context
            new_record = {
                'date': date,
                'student_id': record['student_id'],
                'status': record['status']
            }
            # Add to bulk insert list
            rows_to_insert.append([date, record['student_id'], record['status']])

        try:
            if rows_to_insert:
                sheet.append_rows(rows_to_insert)
            return jsonify({'success': True})
        except Exception as e:
            print(f"Failed to save attendance bulk: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        # Fallback to just mock db if sheets is down
        for record in records:
        return jsonify({'success': True})"""

new_att = """@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('attendance')
    if sheet:
        rows_to_insert = []
        for record in records:
            rows_to_insert.append([date, record['student_id'], record['status']])

        try:
            if rows_to_insert:
                sheet.append_rows(rows_to_insert)
            return jsonify({'success': True})
        except Exception as e:
            print(f"Failed to save attendance bulk: {e}")
            return jsonify({'success': False, 'error': str(e)})
    else:
        print("Failed to save attendance: could not access 'attendance' sheet.")
        return jsonify({'success': False, 'error': 'Sheet not found'})"""

if old_att in content:
    content = content.replace(old_att, new_att)

# Fix student dashboard
old_student_db = """@app.route('/student/dashboard', endpoint='student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')

    # Calculate mock attendance stats for this student
    attendance = [a for a in mock_db['attendance'] if a['student_id'] == student_id]"""

new_student_db = """@app.route('/student/dashboard', endpoint='student_dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('student_id')
    videos = get_data('videos')
    announcements = get_data('announcements')

    attendance_data = get_data('attendance')
    attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]"""

if old_student_db in content:
    content = content.replace(old_student_db, new_student_db)
else:
    # use regex if slight difference
    regex = re.compile(r'# Calculate mock attendance stats for this student\s+attendance = \[a for a in mock_db\[\'attendance\'\] if a\[\'student_id\'\] == student_id\]', re.DOTALL)
    content = re.sub(regex, "attendance_data = get_data('attendance')\n    attendance = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]", content)


old_stud_att = """@app.route('/student/attendance', endpoint='student_attendance_view')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')
    attendance_records = [a for a in mock_db['attendance'] if a['student_id'] == student_id]"""

new_stud_att = """@app.route('/student/attendance', endpoint='student_attendance_view')
@login_required(role='student')
def student_attendance_view():
    student_id = session.get('student_id')
    attendance_data = get_data('attendance')
    attendance_records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]"""

if old_stud_att in content:
    content = content.replace(old_stud_att, new_stud_att)
else:
    regex2 = re.compile(r'attendance_records = \[a for a in mock_db\[\'attendance\'\] if a\[\'student_id\'\] == student_id\]', re.DOTALL)
    content = re.sub(regex2, "attendance_data = get_data('attendance')\n    attendance_records = [a for a in attendance_data if str(a.get('student_id')) == str(student_id)]", content)

with open('app.py', 'w') as f:
    f.write(content)
