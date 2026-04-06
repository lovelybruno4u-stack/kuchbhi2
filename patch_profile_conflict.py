import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace the end of the existing student_profile route with our new logic
old_return = """    completed_vids = len([v for v in video_completion if str(v.get('student_id')) == str(student_id)])

    return render_template('student/profile.html',
                           student=student_data,
                           attendance_percentage=attendance_percentage,
                           total_subjects=len(subjects),
                           total_videos=len(videos),
                           extra_notes=extra_notes,
                           last_active=last_active,
                           points=points,
                           badges=badges,
                           rank=rank,
                           completed_vids=completed_vids,
                           quiz_data=quiz_data)"""

new_return = """    completed_vids = len([v for v in video_completion if str(v.get('student_id')) == str(student_id)])

    # Layer 2 & 8: Digital Academic Passport Metrics
    from modules.momentum import calculate_level, get_level_title, get_xp_for_next_level
    metrics_data = get_data('Student_Metrics')
    my_metrics = next((m for m in metrics_data if str(m.get('student_id')) == str(student_id)), {
        'xp': 0, 'level': 1, 'streak_days': 0, 'reputation_score': 50
    })

    curr_xp = int(my_metrics.get('xp', 0))
    curr_level = calculate_level(curr_xp)
    next_level_xp = get_xp_for_next_level(curr_level)
    prev_level_xp = get_xp_for_next_level(curr_level - 1) if curr_level > 1 else 0

    xp_in_level = curr_xp - prev_level_xp
    xp_needed_total = next_level_xp - prev_level_xp
    progress_pct = (xp_in_level / xp_needed_total * 100) if xp_needed_total > 0 else 0

    badges_list = [b.strip() for b in badges.split(',')] if badges else []

    return render_template('student/profile.html',
                           student=student_data,
                           metrics=my_metrics,
                           title=get_level_title(curr_level),
                           next_level_xp=next_level_xp,
                           progress_pct=min(100, max(0, progress_pct)),
                           badges=badges_list,
                           attendance_percentage=attendance_percentage,
                           total_subjects=len(subjects),
                           total_videos=len(videos),
                           extra_notes=extra_notes,
                           last_active=last_active,
                           points=points,
                           rank=rank,
                           completed_vids=completed_vids,
                           quiz_data=quiz_data)"""

if old_return in content:
    content = content.replace(old_return, new_return)
else:
    print("Could not find the return block in student_profile")

# Remove the duplicate student_profile I appended at the very end of app.py
if "# DIGITAL ACADEMIC PASSPORT" in content:
    idx = content.find("# DIGITAL ACADEMIC PASSPORT")
    # find the end of the duplicate function
    # It's at the end of the file, so just slice it off
    content = content[:idx]
    # Remove any trailing newlines
    content = content.rstrip() + "\n"

with open('app.py', 'w') as f:
    f.write(content)
