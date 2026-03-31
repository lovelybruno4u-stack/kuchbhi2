import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace any lingering mock_db code that was missed
content = re.sub(r'mock_db\[.*?\]\.append\(.*?\)\n', '', content)
content = re.sub(r'mock_db\[.*?\] = \[.*?\]\n', '', content)

# ensure attendance route is clean
old_att_route = """@app.route('/api/teacher/attendance', methods=['POST'])
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

new_att_route = """@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('attendance')
    if sheet:
        rows_to_insert = []
        for record in records:
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
        return jsonify({'success': False, 'error': "Could not connect to Google Sheet"})"""

if old_att_route in content:
    content = content.replace(old_att_route, new_att_route)

with open('app.py', 'w') as f:
    f.write(content)
