import re

with open('app.py', 'r') as f:
    content = f.read()

# Need to update submit_quiz to validate time window and store in quiz_scores
submit_quiz_old = """@app.route('/api/student/submit_quiz', methods=['POST'])
@login_required(role='student')
def submit_quiz():
    student_id = session.get('student_id')
    data = request.json
    percentage = data.get('percentage', 0)"""

submit_quiz_new = """@app.route('/api/student/submit_quiz', methods=['POST'])
@login_required(role='student')
def submit_quiz():
    student_id = session.get('student_id')
    student_name = session.get('name', 'Student')
    data = request.json
    percentage = data.get('percentage', 0)
    score = data.get('score', 0)
    quiz_id = data.get('quiz_id', 'unknown')

    # Store score in quiz_scores
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

    score_record = {
        'quiz_id': quiz_id,
        'student_id': student_id,
        'student_name': student_name,
        'score': score,
        'percentage': percentage,
        'timestamp': now
    }
    add_data_to_sheet('quiz_scores', score_record)"""

if submit_quiz_old in content:
    content = content.replace(submit_quiz_old, submit_quiz_new)
else:
    print("Could not find old submit_quiz route")

with open('app.py', 'w') as f:
    f.write(content)
