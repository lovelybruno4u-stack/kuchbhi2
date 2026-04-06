import re

with open('static/style.css', 'r') as f:
    content = f.read()

premium_css = """
/* ==========================================
   ENTERPRISE PREMIUM UI UPGRADES
   ========================================== */

/* 1. Typography & Spacing */
body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    letter-spacing: -0.01em;
}

/* 2. Skeleton Loaders (replaces spinners for perceived performance) */
.skeleton {
    background: #e2e8f0;
    background: linear-gradient(90deg, #e2e8f0 25%, #f8fafc 50%, #e2e8f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 8px;
}
@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
.skeleton-text { height: 16px; width: 80%; margin-bottom: 8px; }
.skeleton-title { height: 24px; width: 50%; margin-bottom: 16px; }

/* 3. Dark Mode Auto-Detection */
@media (prefers-color-scheme: dark) {
    /* If the user wants dark mode, we can gracefully degrade or implement variables here.
       Since this is a massive change, we'll implement subtle dark hints or allow full override
       in a future phase. For now, ensure contrast is accessible. */
}

/* 4. Smooth Micro-Interactions */
.btn, .glass-card {
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn:active {
    transform: scale(0.97);
}
.glass-card:hover {
    box-shadow: 0 15px 35px rgba(0,0,0,0.06);
    transform: translateY(-2px);
}

/* 5. Focus Mode Styles */
body.focus-mode .sidebar {
    transform: translateX(-100%);
}
body.focus-mode .main-content {
    margin-left: 0;
    max-width: 900px;
    margin: 0 auto;
    padding-top: 5vh;
}
body.focus-mode {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}
.focus-toggle-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--text-primary);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 10px 20px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    z-index: 1000;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s;
}
.focus-toggle-btn:hover {
    transform: scale(1.05);
}

"""

if "ENTERPRISE PREMIUM UI UPGRADES" not in content:
    content += premium_css

with open('static/style.css', 'w') as f:
    f.write(content)
