import re

with open('app.py', 'r') as f:
    content = f.read()

# Fix mark_video_complete to check for existing completion first
old_video = """    current_date = datetime.now().strftime('%Y-%m-%d')

    new_completion = {
        'date': current_date,
        'student_id': student_id,
        'subject': subject,
        'completed': 'Yes'
    }

    add_data_to_sheet('video_completion_V3', new_completion)"""

new_video = """    current_date = datetime.now().strftime('%Y-%m-%d')

    # ANTI-CHEAT: Check if already completed this video
    completed_videos = get_data('video_completion_V3')
    already_done = any(
        str(v.get('student_id')) == str(student_id) and str(v.get('video_id')) == str(video_id)
        for v in completed_videos
    )

    if already_done:
        return jsonify({'success': False, 'error': 'Video points already claimed.'}), 403

    new_completion = {
        'date': current_date,
        'student_id': student_id,
        'subject': subject,
        'video_id': video_id,
        'completed': 'Yes'
    }

    add_data_to_sheet('video_completion_V3', new_completion)"""

if old_video in content:
    content = content.replace(old_video, new_video)
else:
    print("Could not find video anti-cheat hook.")

# Fix submit_task to prevent duplicate
old_task = """@app.route('/student/submit_task/<task_id>', methods=['POST'])
@rate_limit
@login_required(role='student')
def submit_task(task_id):
    student_id = session.get('student_id')
    new_status = {
        'task_id': task_id,
        'student_id': student_id,
        'status': 'Completed'
    }
    add_data_to_sheet('Task_Status_V3', new_status)
    award_points(student_id, 30, "Completed a daily task")"""

new_task = """@app.route('/student/submit_task/<task_id>', methods=['POST'])
@rate_limit
@login_required(role='student')
def submit_task(task_id):
    student_id = session.get('student_id')

    # ANTI-CHEAT: Check if already completed
    task_statuses = get_data('Task_Status_V3')
    already_done = any(
        str(t.get('student_id')) == str(student_id) and str(t.get('task_id')) == str(task_id)
        for t in task_statuses
    )

    if already_done:
        flash("Task already completed.", "warning")
        return redirect(url_for('student_tasks'))

    new_status = {
        'task_id': task_id,
        'student_id': student_id,
        'status': 'Completed'
    }
    add_data_to_sheet('Task_Status_V3', new_status)
    award_points(student_id, 30, "Completed a daily task")"""

if old_task in content:
    content = content.replace(old_task, new_task)
else:
    print("Could not find task anti-cheat hook.")

# Fix mark_dpp_complete to prevent duplicate
old_dpp = """@app.route('/student/mark_dpp_complete/<dpp_id>', methods=['POST'])
@rate_limit
@login_required(role='student')
def mark_dpp_complete(dpp_id):
    student_id = session.get('student_id')
    new_status = {
        'dpp_id': dpp_id,
        'student_id': student_id,
        'status': 'Completed'
    }
    add_data_to_sheet('DPP_Status_V3', new_status)
    award_points(student_id, 20, "Completed DPP")"""

new_dpp = """@app.route('/student/mark_dpp_complete/<dpp_id>', methods=['POST'])
@rate_limit
@login_required(role='student')
def mark_dpp_complete(dpp_id):
    student_id = session.get('student_id')

    # ANTI-CHEAT: Check if already completed
    dpp_statuses = get_data('DPP_Status_V3')
    already_done = any(
        str(d.get('student_id')) == str(student_id) and str(d.get('dpp_id')) == str(dpp_id)
        for d in dpp_statuses
    )

    if already_done:
        flash("DPP already marked complete.", "warning")
        return redirect(url_for('student_dpp'))

    new_status = {
        'dpp_id': dpp_id,
        'student_id': student_id,
        'status': 'Completed'
    }
    add_data_to_sheet('DPP_Status_V3', new_status)
    award_points(student_id, 20, "Completed DPP")"""

if old_dpp in content:
    content = content.replace(old_dpp, new_dpp)
else:
    print("Could not find DPP anti-cheat hook.")

with open('app.py', 'w') as f:
    f.write(content)
