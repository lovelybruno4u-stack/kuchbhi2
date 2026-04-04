import re

with open('app.py', 'r') as f:
    content = f.read()

# Add live leaderboard endpoint
live_leaderboard = """
@app.route('/api/student/leaderboard_live')
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
    return jsonify({'success': True, 'leaderboard': leaderboard})

"""

if "def leaderboard_live():" not in content:
    content = content + live_leaderboard

with open('app.py', 'w') as f:
    f.write(content)
