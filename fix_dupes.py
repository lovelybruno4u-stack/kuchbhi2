with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_teacher_ai = False
in_student_ai = False
teacher_ai_started = False
student_ai_started = False

i = 0
while i < len(lines):
    line = lines[i]
    if "# --- API Endpoints for AI Features (Teacher) ---" in line:
        if not teacher_ai_started:
            new_lines.append(line)
            teacher_ai_started = True
            in_teacher_ai = True
        else:
            in_teacher_ai = True
        i += 1
        continue
    elif "# --- Student Routes (Stubs for now) ---" in line:
        in_teacher_ai = False
    elif "# --- API Endpoints for AI Features (Student) ---" in line:
        if not student_ai_started:
            new_lines.append(line)
            student_ai_started = True
            in_student_ai = True
        else:
            in_student_ai = True
        i += 1
        continue
    elif "# --- Materials Routes ---" in line:
        in_student_ai = False

    if in_teacher_ai:
        if not teacher_ai_started:
            pass # shouldn't happen
    if not in_teacher_ai and not in_student_ai:
        new_lines.append(line)

    i += 1

with open('app_cleaned.py', 'w') as f:
    f.writelines(new_lines)
