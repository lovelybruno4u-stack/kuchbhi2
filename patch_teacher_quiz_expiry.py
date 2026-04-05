import re

with open('templates/teacher/quiz.html', 'r') as f:
    content = f.read()

# Add to the table headers
content = content.replace("<th>Time Window</th>", "<th>Time Window</th>\n                    <th>Leaderboard Expiry</th>")

# Add to the table row
old_table_row = """                    <td>
                        <div style="font-size: 0.85rem;">
                            <span style="color: var(--success);">Start: {{ q.start_time or 'Anytime' }}</span><br>
                            <span style="color: var(--danger);">End: {{ q.end_time or 'Anytime' }}</span>
                        </div>
                    </td>
                    <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">{{ q.question }}</td>"""

new_table_row = """                    <td>
                        <div style="font-size: 0.85rem;">
                            <span style="color: var(--success);">Start: {{ q.start_time or 'Anytime' }}</span><br>
                            <span style="color: var(--danger);">End: {{ q.end_time or 'Anytime' }}</span>
                        </div>
                    </td>
                    <td>
                        <span style="font-size: 0.85rem; color: #6b7280;"><i class="fas fa-hourglass-end"></i> {{ q.score_expiry or 'Never' }}</span>
                    </td>
                    <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">{{ q.question }}</td>"""
if old_table_row in content:
    content = content.replace(old_table_row, new_table_row)

# Add to the form
old_form_group = """                    <div class="form-group">
                        <label>End Time <small>(Submissions locked)</small></label>
                        <input type="datetime-local" id="quiz_end_time" class="form-control" required>
                    </div>"""
new_form_group = """                    <div class="form-group">
                        <label>End Time <small>(Submissions locked)</small></label>
                        <input type="datetime-local" id="quiz_end_time" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Leaderboard Expiry <small>(Delete scores after)</small></label>
                        <input type="datetime-local" id="quiz_score_expiry" class="form-control">
                    </div>"""
if old_form_group in content:
    content = content.replace(old_form_group, new_form_group)

# Add to the payload
old_payload = """            subject: document.getElementById('quiz_subject').value,
            start_time: document.getElementById('quiz_start_time').value,
            end_time: document.getElementById('quiz_end_time').value,
            questions: []"""
new_payload = """            subject: document.getElementById('quiz_subject').value,
            start_time: document.getElementById('quiz_start_time').value,
            end_time: document.getElementById('quiz_end_time').value,
            score_expiry: document.getElementById('quiz_score_expiry').value,
            questions: []"""
if old_payload in content:
    content = content.replace(old_payload, new_payload)

with open('templates/teacher/quiz.html', 'w') as f:
    f.write(content)
