import re

with open('templates/student/student_dashboard.html', 'r') as f:
    content = f.read()

# Add Silent Motivation Banner
silent_motivation = """
<!-- Phase 7: Silent Motivation Engine -->
<div class="glass-card" style="margin-bottom: 24px; padding: 15px 20px; border-left: 4px solid var(--primary-color); display: flex; align-items: center; justify-content: space-between; background: linear-gradient(90deg, var(--white) 0%, #f1f5f9 100%);">
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="background: #e0e7ff; color: #4f46e5; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
            <i class="fas fa-lightbulb"></i>
        </div>
        <div>
            <h4 style="margin: 0 0 4px 0; color: var(--text-primary); font-size: 0.95rem;">Insight</h4>
            <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500;">
                {% if persona.tuning.feedback_tone == 'welcoming' %}
                    You are capable of catching up quickly with just 2 focused sessions this week.
                {% elif persona.tuning.feedback_tone == 'growth_focused' %}
                    Your effort is normalizing. Many students found this phase tricky initially, keep going.
                {% else %}
                    You are consistent this week! You are close to the next XP tier.
                {% endif %}
            </p>
        </div>
    </div>
</div>
"""

if "Phase 7: Silent Motivation Engine" not in content:
    target = '<div class="glass-card" style="margin-bottom: 24px; {% if persona and persona.tuning.dashboard_complexity == \'simplified\' %}display: none;{% endif %}">'
    content = content.replace(target, silent_motivation + "\n" + target)
    print("Added silent motivation banner")

with open('templates/student/student_dashboard.html', 'w') as f:
    f.write(content)
