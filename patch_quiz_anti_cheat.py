import re

with open('app.py', 'r') as f:
    content = f.read()

# Add Anti-Cheat duplicate submission check
old_submit = """        percentage = data.get('percentage', 0)
        score = data.get('score', 0)
        quiz_id = data.get('quiz_id', 'unknown')

        # Store score in quiz_scores
        from datetime import datetime"""

new_submit = """        percentage = data.get('percentage', 0)
        score = data.get('score', 0)
        quiz_id = data.get('quiz_id', 'unknown')

        # ANTI-CHEAT: Check if already submitted
        existing_scores = get_data('quiz_scores')
        has_submitted = any(
            str(s.get('quiz_id')) == str(quiz_id) and str(s.get('student_id')) == str(student_id)
            for s in existing_scores
        )

        if has_submitted:
            return jsonify({'success': False, 'error': 'You have already submitted this quiz. Multiple attempts are not allowed.'}), 403

        # Store score in quiz_scores
        from datetime import datetime"""

if old_submit in content:
    content = content.replace(old_submit, new_submit)
else:
    print("Could not find submit_quiz injection point")

# Update student_quiz route to pass attempted quizzes
old_route = """@app.route('/student/quiz')
@login_required(role='student')
def student_quiz():
    quiz_data = get_data('quiz')
    # Group by subject and date for better UI
    from collections import defaultdict
    quizzes = defaultdict(list)
    for q in quiz_data:
        key = f"{q.get('date', '')} - {q.get('subject', '')}"
        quizzes[key].append(q)
    return render_template('student/quiz.html', quizzes=quizzes)"""

new_route = """@app.route('/student/quiz')
@login_required(role='student')
def student_quiz():
    student_id = session.get('student_id')
    quiz_data = get_data('quiz')

    # Get previously attempted quizzes
    quiz_scores = get_data('quiz_scores')
    attempted_quiz_ids = [str(s.get('quiz_id')) for s in quiz_scores if str(s.get('student_id')) == str(student_id)]

    # Group by subject and date for better UI
    from collections import defaultdict
    quizzes = defaultdict(list)
    for q in quiz_data:
        key = f"{q.get('date', '')} - {q.get('subject', '')}"
        quizzes[key].append(q)

    return render_template('student/quiz.html', quizzes=quizzes, attempted_quiz_ids=attempted_quiz_ids)"""

if old_route in content:
    content = content.replace(old_route, new_route)
else:
    print("Could not find student_quiz route")

with open('app.py', 'w') as f:
    f.write(content)
