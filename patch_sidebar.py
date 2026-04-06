import re

with open('templates/student/base.html', 'r') as f:
    content = f.read()

# Add Profile to Sidebar
if 'href="{{ url_for(\'student_profile\') }}"' not in content:
    old_link = """                <a href="{{ url_for('student_chatbot') }}" class="nav-item {% if request.endpoint == 'student_chatbot' %}active{% endif %}">
                    <i class="fas fa-comments"></i> AI Study Bot
                </a>"""

    new_link = """                <a href="{{ url_for('student_chatbot') }}" class="nav-item {% if request.endpoint == 'student_chatbot' %}active{% endif %}">
                    <i class="fas fa-comments"></i> AI Study Bot
                </a>
                <a href="{{ url_for('student_profile') }}" class="nav-item {% if request.endpoint == 'student_profile' %}active{% endif %}">
                    <i class="fas fa-id-card"></i> Passport / Profile
                </a>"""

    content = content.replace(old_link, new_link)
    print("Added passport to sidebar")

with open('templates/student/base.html', 'w') as f:
    f.write(content)
