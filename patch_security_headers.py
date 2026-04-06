import re

with open('app.py', 'r') as f:
    content = f.read()

headers_code = """
# ==========================================
# ENTERPRISE SECURITY HEADERS
# ==========================================
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Optional: response.headers['Content-Security-Policy'] = "default-src 'self' https: 'unsafe-inline' 'unsafe-eval'"
    return response

"""

if "ENTERPRISE SECURITY HEADERS" not in content:
    target = "@app.errorhandler(Exception)"
    content = content.replace(target, headers_code + target)

with open('app.py', 'w') as f:
    f.write(content)
