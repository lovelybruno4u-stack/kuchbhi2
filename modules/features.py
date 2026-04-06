import os

# Feature Flag Configuration
# In production, these could be loaded from Redis or the DB to toggle live
FLAGS = {
    "ENABLE_XP_SYSTEM": True,
    "ENABLE_SMART_LEADERBOARD": True,
    "ENABLE_FOCUS_MODE": True,
    "ENABLE_TRUSTED_DEVICES": True,
    "ENABLE_SILENT_MOTIVATION": True,
    "ENABLE_ANALYTICS": True
}

def is_feature_enabled(feature_name):
    """Check if an experimental feature is active."""
    return FLAGS.get(feature_name, False)
