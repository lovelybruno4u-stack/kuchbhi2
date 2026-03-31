with open('app.py', 'r') as f:
    content = f.read()

bad = """        else:
            print("Could not initialize DB: no Google Credentials provided.")
            app.config['db_initialized'] = False"""

if bad in content:
    content = content.replace(bad, "")

with open('app.py', 'w') as f:
    f.write(content)
