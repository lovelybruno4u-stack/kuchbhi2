import re

with open('app.py', 'r') as f:
    content = f.read()

limiter_code = """
# ==========================================
# ENTERPRISE RATE LIMITING
# ==========================================
import time

# Simple in-memory rate limiter dictionary: {ip_address: [timestamp1, timestamp2, ...]}
rate_limit_cache = {}
RATE_LIMIT_MAX_REQUESTS = 50
RATE_LIMIT_WINDOW_SECONDS = 60

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        now = time.time()

        # Initialize or clean up old timestamps
        if client_ip not in rate_limit_cache:
            rate_limit_cache[client_ip] = []

        rate_limit_cache[client_ip] = [ts for ts in rate_limit_cache[client_ip] if now - ts < RATE_LIMIT_WINDOW_SECONDS]

        # Check limit
        if len(rate_limit_cache[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Too many requests. Please slow down.'}), 429
            return render_template_string('''
                <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
                <h1>429 Too Many Requests</h1><p>You have exceeded the rate limit. Please try again in a minute.</p>
                </body></html>
            '''), 429

        rate_limit_cache[client_ip].append(now)
        return f(*args, **kwargs)
    return decorated_function

"""

if "ENTERPRISE RATE LIMITING" not in content:
    target = "def login_required(role=None):"
    content = content.replace(target, limiter_code + target)

# Apply to login
if "@app.route('/login', methods=['GET', 'POST'])" in content and "@rate_limit" not in content:
    content = content.replace("@app.route('/login', methods=['GET', 'POST'])\n", "@app.route('/login', methods=['GET', 'POST'])\n@rate_limit\n")

# Apply to an API endpoint like mark_video_complete
if "@app.route('/api/student/submit_quiz', methods=['POST'])" in content:
    content = content.replace("@app.route('/api/student/submit_quiz', methods=['POST'])\n", "@app.route('/api/student/submit_quiz', methods=['POST'])\n@rate_limit\n")


with open('app.py', 'w') as f:
    f.write(content)
