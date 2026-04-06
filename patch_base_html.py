import re

with open('templates/student/base.html', 'r') as f:
    content = f.read()

focus_js = """
<!-- Focus Mode Toggle -->
<button class="focus-toggle-btn" onclick="toggleFocusMode()" id="focusBtn">
    <i class="fas fa-eye"></i> Enter Focus Mode
</button>

<script>
    function toggleFocusMode() {
        document.body.classList.toggle('focus-mode');
        const btn = document.getElementById('focusBtn');
        if (document.body.classList.contains('focus-mode')) {
            btn.innerHTML = '<i class="fas fa-eye-slash"></i> Exit Focus Mode';
            showToast('Focus Mode Enabled. Distractions hidden.', 'success');
        } else {
            btn.innerHTML = '<i class="fas fa-eye"></i> Enter Focus Mode';
            showToast('Focus Mode Disabled.', 'success');
        }
    }
</script>
"""

if "focus-toggle-btn" not in content:
    content = content.replace("</body>", focus_js + "\n</body>")

with open('templates/student/base.html', 'w') as f:
    f.write(content)
