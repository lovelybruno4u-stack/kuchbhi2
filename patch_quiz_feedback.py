import re

with open('app.py', 'r') as f:
    content = f.read()

if "from modules.psychology import get_intelligent_feedback" not in content:
    content = content.replace("from modules.momentum import", "from modules.momentum import process_streak_and_xp\nfrom modules.psychology import get_intelligent_feedback, analyze_student_persona, get_belonging_signal\n")

old_return = """        # Bonus points based on score
        if percentage >= 90:
            points_earned += 50
        elif percentage >= 75:
            points_earned += 30
        elif percentage >= 50:
            points_earned += 15
        else:
            points_earned += 5

        award_points(student_id, points_earned, f"Quiz Attempt ({percentage}%)")

        # Check Quiz Champion badge
        gamification = get_data('gamification')
        sheet = get_google_sheet('gamification')
        if sheet:
            for idx, rec in enumerate(gamification):
                if str(rec.get('student_id')) == str(student_id):
                    badges = str(rec.get('badges') or "")
                    badges_list = [b.strip() for b in badges.split(",") if b.strip()]
                    if "Quiz Champion" not in badges_list:
                        badges_list.append("Quiz Champion")
                        sheet.update_cell(idx + 2, 3, ", ".join(badges_list))
                    break

        return jsonify({'success': True, 'points_earned': points_earned})"""

new_return = """        # Bonus points based on score
        if percentage >= 90:
            points_earned += 50
        elif percentage >= 75:
            points_earned += 30
        elif percentage >= 50:
            points_earned += 15
        else:
            points_earned += 5

        award_points(student_id, points_earned, f"Quiz Attempt ({percentage}%)")

        # Psychological Intelligence Feedback
        intel_feedback = get_intelligent_feedback(percentage)
        belonging_signal = get_belonging_signal()

        # Check Quiz Champion badge
        gamification = get_data('gamification')
        sheet = get_google_sheet('gamification')
        if sheet:
            for idx, rec in enumerate(gamification):
                if str(rec.get('student_id')) == str(student_id):
                    badges = str(rec.get('badges') or "")
                    badges_list = [b.strip() for b in badges.split(",") if b.strip()]
                    if "Quiz Champion" not in badges_list:
                        badges_list.append("Quiz Champion")
                        sheet.update_cell(idx + 2, 3, ", ".join(badges_list))
                    break

        return jsonify({
            'success': True,
            'points_earned': points_earned,
            'intel_msg': intel_feedback['msg'],
            'intel_color': intel_feedback['color'],
            'intel_bg': intel_feedback['bg'],
            'belonging_signal': belonging_signal
        })"""

if old_return in content:
    content = content.replace(old_return, new_return)

with open('app.py', 'w') as f:
    f.write(content)
