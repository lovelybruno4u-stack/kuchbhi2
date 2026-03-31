import re

with open('app.py', 'r') as f:
    content = f.read()

# Remove the before_request completely
regex_setup = re.compile(
    r"@app\.before_request\ndef setup_db\(\):\n    global SPREADSHEET_ID\n    if 'db_initialized' not in app\.config:\n"
    r".*?app\.config\['db_initialized'\] = False",
    re.DOTALL
)

content = re.sub(regex_setup, "", content)

# I should also fix the mock attendance issue
# The user wants to avoid crashes if get_data fails, which I have fixed in get_data (it returns [])

with open('app.py', 'w') as f:
    f.write(content)
