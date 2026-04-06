def calculate_smart_leaderboard(scores_list, target_student_id):
    """
    scores_list: [{'student_id': '123', 'name': 'John', 'xp': 450}, ...]
    Returns dict with top 5, nearby competitors, and percentile.
    """
    if not scores_list:
        return {'top': [], 'nearby': [], 'percentile': 0, 'rank': 0}

    # Sort descending
    sorted_scores = sorted(scores_list, key=lambda x: int(x.get('xp', 0)), reverse=True)

    rank = 0
    total = len(sorted_scores)
    target_idx = -1

    for idx, s in enumerate(sorted_scores):
        if str(s.get('student_id')) == str(target_student_id):
            rank = idx + 1
            target_idx = idx
            break

    if target_idx == -1:
        return {'top': sorted_scores[:5], 'nearby': [], 'percentile': 0, 'rank': 0}

    percentile = round(((total - rank) / total) * 100, 1) if total > 1 else 100.0

    # Nearby: 2 above, 2 below
    start_idx = max(0, target_idx - 2)
    end_idx = min(total, target_idx + 3)

    nearby = []
    for i in range(start_idx, end_idx):
        nearby.append({
            'rank': i + 1,
            'name': sorted_scores[i].get('name'),
            'xp': sorted_scores[i].get('xp'),
            'is_me': (i == target_idx)
        })

    return {
        'top': sorted_scores[:5],
        'nearby': nearby,
        'percentile': percentile,
        'rank': rank
    }

def analyze_student_performance(quiz_scores_list, target_student_id):
    """
    Finds strongest/weakest subject based on raw percentages.
    Requires quiz data to be passed or joined.
    """
    # Simplify for performance: calculate average percentage per quiz_id
    # We would need subject mapping. We can just return stubs for the engine right now.
    pass
