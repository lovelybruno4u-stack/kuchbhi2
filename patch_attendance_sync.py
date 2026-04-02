import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace the async_save_attendance_thread and the route completely
old_regex = re.compile(
    r"def async_save_attendance_thread.*?def save_attendance\(\):.*?return jsonify\(\{.*?success.*?\}\)\n\s+except Exception as e:.*?return jsonify\(\{.*?error.*?\}\)",
    re.DOTALL
)

new_save_att = """@app.route('/api/teacher/attendance', methods=['POST'])
@login_required(role='teacher')
def save_attendance():
    data = request.json
    date = data.get('date')
    records = data.get('records', [])

    sheet = get_google_sheet('ATTENDANCE_V2')
    if not sheet:
        return jsonify({'success': False, 'error': "Could not connect to Google Sheet"})

    try:
        from datetime import datetime
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        all_records = sheet.get_all_records()
        headers = sheet.row_values(1)
        if not headers:
            headers = ['student_id', 'student_name', 'class', 'date', 'status', 'last_updated']

        students_info = {str(s.get('id')): s for s in get_data('students')}

        record_map = {}
        for r in all_records:
            key = f"{r.get('student_id')}_{r.get('date')}"
            record_map[key] = r

        for record in records:
            s_id = str(record['student_id'])
            status = '1' if record['status'] == 'Present' else '0'
            s_name = students_info.get(s_id, {}).get('name', 'Unknown')
            s_class = students_info.get(s_id, {}).get('class', '')

            key = f"{s_id}_{date}"

            if key in record_map:
                record_map[key]['status'] = status
                record_map[key]['last_updated'] = last_updated
                record_map[key]['student_name'] = s_name
                record_map[key]['class'] = s_class
            else:
                record_map[key] = {
                    'student_id': s_id,
                    'student_name': s_name,
                    'class': s_class,
                    'date': date,
                    'status': status,
                    'last_updated': last_updated
                }

            if status == '1':
                award_points(s_id, 5, "Attendance")

        new_sheet_data = [headers]
        for key, rec in record_map.items():
            row = [str(rec.get(h, '')) for h in headers]
            new_sheet_data.append(row)

        sheet.clear()
        sheet.update(new_sheet_data)

        invalidate_cache('ATTENDANCE_V2')
        refresh_local_cache()

        return jsonify({'success': True, 'message': 'Attendance saved successfully'})
    except Exception as e:
        print(f"Failed to save Attendance_V2: {e}")
        return jsonify({'success': False, 'error': str(e)})"""

content = re.sub(old_regex, new_save_att, content)

with open('app.py', 'w') as f:
    f.write(content)
