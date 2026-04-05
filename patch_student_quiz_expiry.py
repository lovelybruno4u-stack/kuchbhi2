import re

with open('templates/student/quiz.html', 'r') as f:
    content = f.read()

# Update the HTML layout for Leaderboard
old_lb_html = """    <!-- Live Leaderboard Sidebar -->
    <div>
        <h3 style="margin-bottom: 20px; color: var(--text-primary);"><i class="fas fa-satellite-dish" style="color: var(--danger);"></i> Live Leaderboard</h3>
        <div class="glass-card" style="padding: 15px; background: var(--white);">
            <div id="live-leaderboard">
                <p style="text-align: center; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Fetching live ranks...</p>
            </div>
        </div>
    </div>"""

new_lb_html = """    <!-- Live Leaderboard Sidebar -->
    <div>
        <h3 style="margin-bottom: 20px; color: var(--text-primary);"><i class="fas fa-satellite-dish" style="color: var(--danger);"></i> Live Leaderboard</h3>
        <div class="glass-card" style="padding: 15px; background: var(--white);">
            <div class="form-group" style="margin-bottom: 15px;">
                <label style="font-size: 0.85rem; color: var(--text-secondary);">Select Quiz Leaderboard</label>
                <select id="leaderboard-quiz-select" class="form-control" onchange="fetchLiveLeaderboard()">
                    <option value="">Global Gamification Ranking</option>
                    {% for quiz_title, questions in quizzes.items() %}
                    <option value="{{ questions[0].id }}">Live: {{ quiz_title }}</option>
                    {% endfor %}
                </select>
            </div>
            <div id="live-leaderboard">
                <p style="text-align: center; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Fetching live ranks...</p>
            </div>
        </div>
    </div>"""

if old_lb_html in content:
    content = content.replace(old_lb_html, new_lb_html)

# Update fetchLiveLeaderboard JS
old_fetch = """    function fetchLiveLeaderboard() {
        fetch('/api/student/leaderboard_live')"""

new_fetch = """    function fetchLiveLeaderboard() {
        const quizId = document.getElementById('leaderboard-quiz-select')?.value || '';
        fetch('/api/student/leaderboard_live?quiz_id=' + quizId)"""

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)

# Update the display logic
old_display = """                if(data.success) {"""
new_display = """                if(data.success) {
                    if (data.type === 'expired') {
                        document.getElementById('live-leaderboard').innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px;"><i class="fas fa-hourglass-end" style="font-size: 2rem; margin-bottom: 10px;"></i><p>This leaderboard has expired and is no longer available.</p></div>';
                        return;
                    }
                    if (data.leaderboard.length === 0) {
                        document.getElementById('live-leaderboard').innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No scores yet.</p>';
                        return;
                    }"""

if old_display in content:
    content = content.replace(old_display, new_display)

# Change points display to handle "pts" or "score"
old_pts = """                                <span style="font-weight: 600;">${user.points} pts</span>"""
new_pts = """                                <span style="font-weight: 600;">${user.points} ${data.type === 'global' ? 'pts' : 'score'}</span>"""

if old_pts in content:
    content = content.replace(old_pts, new_pts)

with open('templates/student/quiz.html', 'w') as f:
    f.write(content)
