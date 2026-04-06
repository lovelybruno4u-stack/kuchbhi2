with open('app.py', 'r') as f:
    content = f.read()

# Fix the placement! I put it after a decorator, breaking the syntax.
broken = """@with_exponential_backoff(max_retries=3)

# ==========================================
# ENTERPRISE XSS SANITIZATION
# ==========================================
import html

def sanitize_input(data):
    if isinstance(data, str):
        return html.escape(data.strip())
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(i) for i in data]
    return data

def add_data_to_sheet(sheet_name, row_dict):"""

fixed = """
# ==========================================
# ENTERPRISE XSS SANITIZATION
# ==========================================
import html

def sanitize_input(data):
    if isinstance(data, str):
        return html.escape(data.strip())
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(i) for i in data]
    return data

@with_exponential_backoff(max_retries=3)
def add_data_to_sheet(sheet_name, row_dict):"""

content = content.replace(broken, fixed)

with open('app.py', 'w') as f:
    f.write(content)
