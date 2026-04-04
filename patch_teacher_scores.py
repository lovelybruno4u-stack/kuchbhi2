import re

with open('app.py', 'r') as f:
    content = f.read()

# Add teacher quiz scores route
teacher_scores = """
@app.route('/teacher/quiz_scores')
@login_required(role='teacher')
def teacher_quiz_scores():
    scores = get_data('quiz_scores')
    # Sort by timestamp descending
    scores = sorted(scores, key=lambda x: x.get('timestamp', ''), reverse=True)
    return render_template('teacher/quiz_scores.html', scores=scores)
"""

if "def teacher_quiz_scores():" not in content:
    content = content + teacher_scores

with open('app.py', 'w') as f:
    f.write(content)
