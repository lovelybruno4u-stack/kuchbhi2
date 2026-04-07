import re

with open('templates/student/quiz.html', 'r') as f:
    content = f.read()

# Conditionally disable the form if already attempted
old_form = """                <form class="quiz-form" onsubmit="submitQuiz(event, this, '{{ first_q.id }}')">
                    <div class="questions-list">
                        {% for q in questions %}"""

new_form = """                {% set is_attempted = first_q.id in attempted_quiz_ids %}

                {% if is_attempted %}
                <div style="background: #ecfdf5; border: 1px solid #10b981; color: #065f46; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: 600;">
                    <i class="fas fa-check-circle" style="font-size: 1.5rem; margin-bottom: 5px;"></i><br>
                    You have already completed this quiz. Check your score on the leaderboard.
                </div>
                {% endif %}

                <form class="quiz-form" {% if not is_attempted %}onsubmit="submitQuiz(event, this, '{{ first_q.id }}')"{% endif %}>
                    <div class="questions-list" style="{% if is_attempted %}opacity: 0.6; pointer-events: none;{% endif %}">
                        {% for q in questions %}"""

if old_form in content:
    content = content.replace(old_form, new_form)

old_submit_btn = """                    <div class="quiz-result" style="display: none; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-weight: 600; text-align: center; font-size: 1.2rem;"></div>

                    <button type="submit" class="btn btn-primary submit-quiz-btn" style="width: 100%;"><i class="fas fa-check"></i> Submit Quiz</button>
                </form>"""

new_submit_btn = """                    <div class="quiz-result" style="display: none; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-weight: 600; text-align: center; font-size: 1.2rem;"></div>

                    {% if not is_attempted %}
                    <button type="submit" class="btn btn-primary submit-quiz-btn" style="width: 100%;"><i class="fas fa-check"></i> Submit Quiz</button>
                    {% endif %}
                </form>"""

if old_submit_btn in content:
    content = content.replace(old_submit_btn, new_submit_btn)

with open('templates/student/quiz.html', 'w') as f:
    f.write(content)
