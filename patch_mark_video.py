import re

with open('app.py', 'r') as f:
    content = f.read()

# I messed up when doing the replace logic, it affected mark_video_complete as well!
# Lines 1288-1291 shouldn't be there for mark_video_complete, they replaced the original return jsonify.

old_mark_video_err = """    award_points(student_id, points_earned, f"Completed Video: {subject}")

        return jsonify({'success': True, 'points_earned': points_earned})
    except Exception as e:
        print("Submit quiz error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500"""

new_mark_video_err = """    award_points(student_id, points_earned, f"Completed Video: {subject}")

    return jsonify({'success': True, 'points_earned': points_earned})"""

if old_mark_video_err in content:
    content = content.replace(old_mark_video_err, new_mark_video_err)

with open('app.py', 'w') as f:
    f.write(content)
