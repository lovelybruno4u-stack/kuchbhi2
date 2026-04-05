import re

with open('app.py', 'r') as f:
    content = f.read()

global_err_handler = """
# ==========================================
# GLOBAL HARDENED ERROR HANDLING
# ==========================================
import traceback
from werkzeug.exceptions import HTTPException

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors (like 404s, 401s)
    if isinstance(e, HTTPException):
        # We can handle them gracefully or pass them through
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': e.description}), e.code
        return f"<h1>Error {e.code}</h1><p>{e.description}</p>", e.code

    # Handle completely unhandled Server Errors (500)
    print("FATAL UNHANDLED EXCEPTION:", traceback.format_exc())

    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'The server encountered an internal error. Please try again later.'
        }), 500

    # For UI routes, show a nice premium fallback rather than a crash log
    return render_template_string('''
        <html>
            <head>
                <title>System Error | Ashwathama Classes</title>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
                <style>
                    body { font-family: 'Poppins', sans-serif; background: #f8fafc; color: #1e293b; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.05); text-align: center; max-width: 500px; }
                    h1 { color: #dc2626; margin-bottom: 10px; font-weight: 800; font-size: 2.5rem; }
                    p { color: #64748b; margin-bottom: 30px; line-height: 1.6; }
                    a { display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 12px; font-weight: 600; transition: all 0.3s; }
                    a:hover { background: #4338ca; transform: translateY(-2px); }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Oops!</h1>
                    <p>Our servers encountered an unexpected glitch. Our engineers have been notified and are on it.<br><br>Don't worry, your data is safe.</p>
                    <a href="/login">Return to Home</a>
                </div>
            </body>
        </html>
    '''), 500

"""

if "GLOBAL HARDENED ERROR HANDLING" not in content:
    # Inject it right after app = Flask(__name__) configurations
    target = "app.permanent_session_lifetime = timedelta(days=365)"
    content = content.replace(target, target + "\n" + global_err_handler)

with open('app.py', 'w') as f:
    f.write(content)
