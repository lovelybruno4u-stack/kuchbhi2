import re

with open('templates/student/my_videos.html', 'r') as f:
    content = f.read()

old_js = """document.querySelectorAll('.complete-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        this.disabled = true;"""

new_js = """document.querySelectorAll('.complete-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        if (!confirm("Wait... are you absolutely sure you watched the whole thing? Be truthful! 🤨 The system knows... just kidding, but your conscience does!")) {
            return;
        }

        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        this.disabled = true;"""

if old_js in content:
    content = content.replace(old_js, new_js)
    print("Patched video complete JS")
else:
    print("Could not find video complete JS")

with open('templates/student/my_videos.html', 'w') as f:
    f.write(content)
