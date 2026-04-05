import re

with open('app.py', 'r') as f:
    content = f.read()

# I need to indent the body of submit_quiz properly under `try:`
old_body = """    # Store score in quiz_scores
    from datetime import datetime"""

new_body = """        # Store score in quiz_scores
        from datetime import datetime"""

content = content.replace("""    # Store score in quiz_scores
    from datetime import datetime
    import pytz
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

    score_record = {
        'quiz_id': quiz_id,
        'student_id': student_id,
        'student_name': student_name,
        'score': score,
        'percentage': percentage,
        'timestamp': now
    }
    add_data_to_sheet('quiz_scores', score_record)

    # +10 for participation
    points_earned = 10

    # Bonus points based on score
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
                break""", """        # Store score in quiz_scores
        from datetime import datetime
        import pytz
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        score_record = {
            'quiz_id': quiz_id,
            'student_id': student_id,
            'student_name': student_name,
            'score': score,
            'percentage': percentage,
            'timestamp': now
        }
        success_insert = add_data_to_sheet('quiz_scores', score_record)
        if not success_insert:
            raise Exception("Failed to append quiz score to Google Sheets")

        # +10 for participation
        points_earned = 10

        # Bonus points based on score
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
                    break""")

with open('app.py', 'w') as f:
    f.write(content)
