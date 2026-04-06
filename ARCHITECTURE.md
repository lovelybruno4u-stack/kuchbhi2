# Ashwathama Classes - Enterprise Transformation Architecture

## 1. System Design Overview
The platform transitions from a monolithic Flask application into a highly modular, feature-flagged architecture.
This ensures zero regressions on core functionality while testing new psychological and gamification engines.

- **Core Module (`app.py`)**: Handles core routing, auth, and database connections.
- **Extensions (`modules/`)**: Isolated logic for Analytics, Momentum (XP/Levels), and Smart Leaderboards.
- **Feature Flag Layer**: Controls rolling out features (e.g., `FOCUS_MODE_ENABLED`, `XP_SYSTEM_ENABLED`) allowing instant fallback without deploying code.

## 2. Database Changes (Google Sheets Backward-Compatible)
We maintain existing schemas (`students`, `quiz`, etc.) and append a new dedicated schema:
- **`Student_Metrics`**:
  `['student_id', 'xp', 'level', 'streak_days', 'last_active', 'reputation_score', 'trusted_devices']`

## 3. Implementation Order
1. **Infrastructure**: Add Feature Flag layer and `Student_Metrics` DB schema.
2. **Backend Engines**: Implement `momentum.py` (XP/Streaks) and `analytics.py` (Percentiles/Nearby Ranks).
3. **API Integration**: Hook engines into `app.py` behind feature flags.
4. **UI Overhaul**: Introduce Focus Mode, Skeleton Loaders, and Premium Typography in CSS.
5. **Interactive UI**: Build the Digital Academic Passport and Smart Leaderboard views.

## 4. Risk Analysis
- **API Limits**: Fetching extensive analytics could trigger Google Sheets `429` errors.
  *Mitigation*: Heavily cache the `Student_Metrics` and Leaderboard calculations in-memory for 5 minutes. Use batch updates.
- **UI Performance**: Complex DOM updates for nearby competitors could lag mobile.
  *Mitigation*: Use pure CSS transitions, skeleton loaders, and asynchronous vanilla JS.
- **Auth Integrity**: Adding WebAuthn/Trusted Devices could lock out students.
  *Mitigation*: Password login remains the primary absolute fallback. Device trust is an additive layer.
