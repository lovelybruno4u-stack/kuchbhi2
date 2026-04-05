import os
import re

# We will search through all JS in HTML files and replace alert('...') with showToast('...', 'error') or 'success' depending on context

def add_toast_css_and_js(content):
    toast_css = """
/* Premium Toast Notifications */
#toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 10px;
    pointer-events: none;
}
.premium-toast {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 16px 24px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    border-left: 5px solid var(--primary-color);
    transform: translateX(120%);
    opacity: 0;
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 500;
    pointer-events: auto;
    min-width: 250px;
}
.premium-toast.show {
    transform: translateX(0);
    opacity: 1;
}
.premium-toast.error { border-left-color: var(--danger); }
.premium-toast.success { border-left-color: var(--success); }
.premium-toast.warning { border-left-color: var(--warning); }
.premium-toast i { font-size: 1.2rem; }
.premium-toast.error i { color: var(--danger); }
.premium-toast.success i { color: var(--success); }
.premium-toast.warning i { color: var(--warning); }
"""
    toast_js = """
// Premium Toast Notification System
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `premium-toast ${type}`;

    let icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    if (type === 'warning') icon = 'fa-exclamation-triangle';

    toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto-remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// Override default window.alert globally for absolute polish
window.originalAlert = window.alert;
window.alert = function(message) {
    showToast(message, 'warning'); // Default fallback is warning
};
"""
    if "/* Premium Toast Notifications */" not in content:
        # insert css before closing head
        content = content.replace("</head>", f"<style>{toast_css}</style>\n</head>")

    if "function showToast" not in content:
        # insert js before closing body
        content = content.replace("</body>", f"<script>{toast_js}</script>\n</body>")

    return content

for path in ['templates/student/base.html', 'templates/teacher/base.html']:
    with open(path, 'r') as f:
        content = f.read()
    content = add_toast_css_and_js(content)
    with open(path, 'w') as f:
        f.write(content)
