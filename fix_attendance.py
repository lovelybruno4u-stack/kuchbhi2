with open('app.py', 'r') as f:
    content = f.read()

bad_block = """    else:
        # Fallback to just mock db if sheets is down
        for record in records:
                'date': date,
                'student_id': record['student_id'],
                'status': record['status']
            })
        return jsonify({'success': True})"""

good_block = """    else:
        return jsonify({'success': False, 'error': 'Cannot save: Sheet not found'})"""

if bad_block in content:
    content = content.replace(bad_block, good_block)

with open('app.py', 'w') as f:
    f.write(content)
