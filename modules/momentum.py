import math
from datetime import datetime
import pytz

def calculate_level(xp):
    """
    Gradual curve:
    Level 1: 0 XP
    Level 5: ~1000 XP
    Level 10: ~4000 XP
    Level 20: ~15000 XP
    """
    if xp < 0: return 1
    # Simple quadratic curve: XP = (Level - 1)^2 * 40
    # Level = sqrt(XP/40) + 1
    level = math.floor((math.sqrt(xp / 40.0))) + 1
    return min(level, 50) # Cap at 50

def get_level_title(level):
    if level < 5: return "Beginner"
    if level < 10: return "Scholar"
    if level < 15: return "Achiever"
    if level < 20: return "Mastermind"
    return "Ranker"

def get_xp_for_next_level(current_level):
    return (current_level) ** 2 * 40

def process_streak_and_xp(student_id, current_metrics, action='login', score=0):
    """
    Pure function to calculate new metrics based on an action.
    actions: 'login', 'quiz', 'task'
    """
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today_str = now.strftime('%Y-%m-%d')

    xp = int(current_metrics.get('xp', 0))
    streak = int(current_metrics.get('streak_days', 0))
    last_active = current_metrics.get('last_active_date', '')
    rep = int(current_metrics.get('reputation_score', 50)) # Start at neutral 50

    silent_messages = []

    # Process Streak
    if last_active != today_str:
        if last_active:
            try:
                last_dt = datetime.strptime(last_active, '%Y-%m-%d')
                days_diff = (now.replace(tzinfo=None) - last_dt).days
                if days_diff == 1:
                    streak += 1
                    if streak in [3, 5, 7, 14, 30, 50, 100]:
                        silent_messages.append(f"🔥 Amazing! You've hit a {streak}-day study streak!")
                else:
                    streak = 1 # Reset
                    silent_messages.append("Welcome back! Let's build a new study streak.")
            except:
                streak = 1
        else:
            streak = 1

        # Daily login XP
        xp += 20
        rep = min(100, rep + 1) # Reliability goes up

    # Process Actions
    if action == 'quiz':
        xp += 10 # Base participation
        if score >= 90: xp += 50
        elif score >= 75: xp += 30
        elif score >= 50: xp += 15
        rep = min(100, rep + 2) # High reliability for taking tests

    old_level = calculate_level(int(current_metrics.get('xp', 0)))
    new_level = calculate_level(xp)

    if new_level > old_level:
        silent_messages.append(f"🎉 Level Up! You are now a Level {new_level} {get_level_title(new_level)}.")

    return {
        'xp': xp,
        'level': new_level,
        'streak_days': streak,
        'last_active_date': today_str,
        'reputation_score': rep,
        'messages': silent_messages
    }
