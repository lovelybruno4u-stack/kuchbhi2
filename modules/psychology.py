from datetime import datetime
import pytz

# ==============================================================================
# PSYCHOLOGICAL INTELLIGENCE ENGINE
# Transforms raw data into behavioral insights to drive UI/UX adaptation.
# ==============================================================================

def analyze_student_persona(student_id, current_metrics, recent_quiz_scores=None):
    """
    Infers the student's psychological state based on pure behavioral signals.
    """
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)

    streak = int(current_metrics.get('streak_days', 0))
    last_active = current_metrics.get('last_active_date', '')
    xp = int(current_metrics.get('xp', 0))

    days_inactive = 0
    if last_active:
        try:
            last_dt = datetime.strptime(last_active, '%Y-%m-%d')
            days_inactive = (now.replace(tzinfo=None) - last_dt).days
        except Exception:
            pass

    # Calculate average recent score to detect struggle
    avg_score = 100
    if recent_quiz_scores:
        scores = [float(s.get('percentage', 0)) for s in recent_quiz_scores]
        if scores:
            avg_score = sum(scores) / len(scores)

    # --------------------------------------------------
    # INFER BEHAVIORAL PROFILE
    # --------------------------------------------------
    persona = "standard"
    if days_inactive > 4:
        persona = "inactive_returner" # Needs frictionless restart, low cognitive load
    elif streak > 5 and avg_score > 80:
        persona = "consistent_achiever" # Needs deep challenge, mastery insights
    elif streak > 3 and avg_score < 60:
        persona = "high_effort_struggler" # Needs confidence stabilization, error pattern insights
    elif streak <= 2 and xp > 1000:
        persona = "irregular_performer" # Needs consistency nudges
    elif avg_score < 40 and len(recent_quiz_scores or []) > 2:
        persona = "anxious_tester" # Needs private progress framing, hidden top leaderboards

    # --------------------------------------------------
    # ADAPTIVE UX TUNING VARIABLES
    # --------------------------------------------------
    tuning = {
        'dashboard_complexity': 'standard',
        'leaderboard_view': 'standard',
        'focus_duration_mins': 25,
        'feedback_tone': 'encouraging'
    }

    if persona == "inactive_returner":
        tuning['dashboard_complexity'] = 'simplified'
        tuning['leaderboard_view'] = 'hidden' # Hide to reduce comparison stress on return
        tuning['focus_duration_mins'] = 15 # Short, easy restart session
        tuning['feedback_tone'] = 'welcoming'

    elif persona == "anxious_tester" or persona == "high_effort_struggler":
        tuning['leaderboard_view'] = 'nearby_only' # Hide top rankers, show local growth
        tuning['feedback_tone'] = 'growth_focused'

    elif persona == "consistent_achiever":
        tuning['leaderboard_view'] = 'percentile_and_top'
        tuning['focus_duration_mins'] = 50 # Deep work capability
        tuning['feedback_tone'] = 'challenge_focused'

    return {
        'persona': persona,
        'tuning': tuning,
        'days_inactive': days_inactive
    }

def get_intelligent_feedback(percentage):
    """
    Replaces judgmental generic feedback with growth-oriented language.
    """
    p = float(percentage)
    if p >= 90:
        return {
            'msg': "High mastery level. Ready for advanced conceptual challenges.",
            'color': '#065f46',
            'bg': '#d1fae5'
        }
    elif p >= 75:
        return {
            'msg': "Solid foundation built. Minor revisions will close the gap.",
            'color': '#0f766e',
            'bg': '#ccfbf1'
        }
    elif p >= 50:
        return {
            'msg': "Early stage mastery. You're grasping the core logic, concepts are still forming.",
            'color': '#92400e',
            'bg': '#fef3c7'
        }
    else:
        return {
            'msg': "Growth opportunity identified. This topic usually clicks after 2 focused revision sessions.",
            'color': '#1e3a8a', # Not red (danger). Blue for learning.
            'bg': '#dbeafe'
        }

def get_belonging_signal():
    import random
    signals = [
        "Many students find this phase challenging initially—you're on the right track.",
        "Class momentum is improving this week. Keep going!",
        "Students with similar patterns mastered this through consistent small steps.",
        "Your effort is building a solid foundation."
    ]
    return random.choice(signals)
