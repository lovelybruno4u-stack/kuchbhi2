import re

with open('app.py', 'r') as f:
    content = f.read()

profile_route = """
# ==========================================
# DIGITAL ACADEMIC PASSPORT
# ==========================================
from modules.momentum import calculate_level, get_level_title, get_xp_for_next_level

@app.route('/student/profile')
@login_required(role='student')
def student_profile():
    student_id = session.get('student_id')
    students = get_data('students')
    student = next((s for s in students if str(s.get('id')) == str(student_id)), {})

    # Get gamification data for badges
    gamification = get_data('gamification')
    my_gami = next((g for g in gamification if str(g.get('student_id')) == str(student_id)), {})
    badges_str = my_gami.get('badges', '')
    badges = [b.strip() for b in badges_str.split(',')] if badges_str else []

    # Get metrics
    metrics = get_data('Student_Metrics')
    my_metrics = next((m for m in metrics if str(m.get('student_id')) == str(student_id)), {
        'xp': 0, 'level': 1, 'streak_days': 0, 'reputation_score': 50
    })

    # Calculate progress bar
    curr_xp = int(my_metrics.get('xp', 0))
    curr_level = calculate_level(curr_xp)
    next_level_xp = get_xp_for_next_level(curr_level)
    prev_level_xp = get_xp_for_next_level(curr_level - 1) if curr_level > 1 else 0

    xp_in_level = curr_xp - prev_level_xp
    xp_needed_total = next_level_xp - prev_level_xp

    progress_pct = (xp_in_level / xp_needed_total * 100) if xp_needed_total > 0 else 0

    return render_template('student/profile.html',
                           student=student,
                           metrics=my_metrics,
                           title=get_level_title(curr_level),
                           next_level_xp=next_level_xp,
                           progress_pct=min(100, max(0, progress_pct)),
                           badges=badges)
"""

if "def student_profile():" not in content:
    content += "\n" + profile_route

with open('app.py', 'w') as f:
    f.write(content)
