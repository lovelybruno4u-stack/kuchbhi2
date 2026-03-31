with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.strip() == "else:" and len(new_lines) > 0 and "app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')" in new_lines[-1]:
        skip = True
    elif skip and "app.config['db_initialized'] = False" in line:
        skip = False
        continue

    if not skip:
        new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)
