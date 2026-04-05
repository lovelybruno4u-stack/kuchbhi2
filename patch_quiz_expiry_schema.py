import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update Schema
if "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time', 'score_expiry']," not in content:
    content = content.replace(
        "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time'],",
        "'quiz': ['id', 'date', 'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'start_time', 'end_time', 'score_expiry'],"
    )

# 2. Update add_quiz
old_add_quiz_extract = """    date = data.get('date')
    subject = data.get('subject')
    start_time = data.get('start_time')
    end_time = data.get('end_time')"""

new_add_quiz_extract = """    date = data.get('date')
    subject = data.get('subject')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    score_expiry = data.get('score_expiry')"""

if old_add_quiz_extract in content:
    content = content.replace(old_add_quiz_extract, new_add_quiz_extract)

old_new_q = """            'answer': q.get('answer'),
            'start_time': start_time,
            'end_time': end_time
        }"""

new_new_q = """            'answer': q.get('answer'),
            'start_time': start_time,
            'end_time': end_time,
            'score_expiry': score_expiry
        }"""

if old_new_q in content:
    content = content.replace(old_new_q, new_new_q)

# 3. Update leaderboard_live
old_leaderboard = """@app.route('/api/student/leaderboard_live')
@login_required(role='student')
def leaderboard_live():
    # Provide the current gamification leaderboard for live updates
    gamification = get_data('gamification')
    students = get_data('students')
    student_map = {str(s.get('id')): s.get('name', 'Unknown') for s in students}

    leaderboard = []
    for g in gamification:
        sid = str(g.get('student_id'))
        name = student_map.get(sid, 'Unknown')
        pts = int(g.get('points', 0))
        leaderboard.append({'name': name, 'points': pts})

    leaderboard = sorted(leaderboard, key=lambda x: x['points'], reverse=True)[:10]
    return jsonify({'success': True, 'leaderboard': leaderboard})"""

new_leaderboard = """@app.route('/api/student/leaderboard_live')
@login_required(role='student')
def leaderboard_live():
    quiz_id = request.args.get('quiz_id')

    if not quiz_id:
        # Default global gamification leaderboard
        gamification = get_data('gamification')
        students = get_data('students')
        student_map = {str(s.get('id')): s.get('name', 'Unknown') for s in students}

        leaderboard = []
        for g in gamification:
            sid = str(g.get('student_id'))
            name = student_map.get(sid, 'Unknown')
            pts = int(g.get('points', 0))
            leaderboard.append({'name': name, 'points': pts})

        leaderboard = sorted(leaderboard, key=lambda x: x['points'], reverse=True)[:10]
        return jsonify({'success': True, 'leaderboard': leaderboard, 'type': 'global'})
    else:
        # Specific quiz leaderboard
        scores = get_data('quiz_scores')
        quiz_data = get_data('quiz')

        # Check expiry
        expiry = None
        for q in quiz_data:
            if str(q.get('id')) == str(quiz_id):
                expiry = q.get('score_expiry')
                break

        if expiry and str(expiry).lower() != 'none':
            from datetime import datetime
            import pytz
            tz = pytz.timezone('Asia/Kolkata')
            now = datetime.now(tz)
            try:
                expiry_dt = datetime.strptime(str(expiry), '%Y-%m-%dT%H:%M')
                expiry_dt = tz.localize(expiry_dt)
                if now > expiry_dt:
                    return jsonify({'success': True, 'leaderboard': [], 'type': 'expired'})
            except Exception as e:
                print("Expiry parse error:", e)

        # Filter scores for this quiz
        quiz_scores = [s for s in scores if str(s.get('quiz_id')) == str(quiz_id)]

        leaderboard = []
        for s in quiz_scores:
            leaderboard.append({'name': s.get('student_name', 'Student'), 'points': int(s.get('score', 0))})

        leaderboard = sorted(leaderboard, key=lambda x: x['points'], reverse=True)[:10]
        return jsonify({'success': True, 'leaderboard': leaderboard, 'type': 'quiz'})"""

if old_leaderboard in content:
    content = content.replace(old_leaderboard, new_leaderboard)

with open('app.py', 'w') as f:
    f.write(content)
