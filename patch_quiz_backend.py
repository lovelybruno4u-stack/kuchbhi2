import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace the single add_quiz route with a batch one that accepts JSON
add_quiz_old = """@app.route('/teacher/add_quiz', methods=['POST'])
@login_required(role='teacher')
def add_quiz():
    import uuid
    new_q = {
        'id': str(uuid.uuid4())[:8],
        'date': request.form.get('date'),
        'subject': request.form.get('subject'),
        'question': request.form.get('question'),
        'option1': request.form.get('option1'),
        'option2': request.form.get('option2'),
        'option3': request.form.get('option3'),
        'option4': request.form.get('option4'),
        'answer': request.form.get('answer')
    }
    add_data_to_sheet('quiz', new_q)
    flash('Quiz question added!', 'success')
    return redirect(url_for('teacher_quiz'))"""

add_quiz_new = """@app.route('/teacher/add_quiz', methods=['POST'])
@login_required(role='teacher')
def add_quiz():
    import uuid
    data = request.json
    if not data or 'questions' not in data:
        return jsonify({'success': False, 'error': 'No questions provided'}), 400

    date = data.get('date')
    subject = data.get('subject')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    # We will generate a unique "batch ID" or just use random IDs for questions
    # But tying them together visually is usually done by date + subject
    # A single shared Quiz ID for this session might be good, let's use the first 8 chars of a uuid
    quiz_group_id = str(uuid.uuid4())[:8]

    new_questions = []
    for q in data['questions']:
        new_q = {
            'id': quiz_group_id, # Shared ID for grouping the quiz
            'date': date,
            'subject': subject,
            'question': q.get('question'),
            'option1': q.get('option1'),
            'option2': q.get('option2'),
            'option3': q.get('option3'),
            'option4': q.get('option4'),
            'answer': q.get('answer'),
            'start_time': start_time,
            'end_time': end_time
        }
        new_questions.append(new_q)
        add_data_to_sheet('quiz', new_q) # Using the existing helper, though bulk add would be better

    return jsonify({'success': True, 'message': f'{len(new_questions)} questions added successfully.'})"""

if add_quiz_old in content:
    content = content.replace(add_quiz_old, add_quiz_new)
else:
    print("Could not find old add_quiz route")

# Update student_quiz group by to use quiz_id + subject + date?
# Actually, the old one grouped by date_subject: `key = f"{q.get('date')} - {q.get('subject')}"`
# This is fine for now, we'll keep that but send start_time and end_time.

with open('app.py', 'w') as f:
    f.write(content)
