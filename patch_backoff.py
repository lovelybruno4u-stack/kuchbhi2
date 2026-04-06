import re

with open('app.py', 'r') as f:
    content = f.read()

backoff_code = """
# ==========================================
# ENTERPRISE GOOGLE SHEETS BACKOFF
# ==========================================
import random
from functools import wraps

def with_exponential_backoff(max_retries=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # If it's the last attempt, raise the error
                    if attempt == max_retries - 1:
                        print(f"FAILED after {max_retries} attempts: {func.__name__} - {e}")
                        raise e

                    # Wait before retrying (exponential backoff with jitter)
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 0.5)
                    print(f"WARN: {func.__name__} failed (attempt {attempt+1}/{max_retries}). Retrying in {delay:.2f}s... Error: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

"""

if "ENTERPRISE GOOGLE SHEETS BACKOFF" not in content:
    target = "def get_google_sheet(sheet_name):"
    content = content.replace(target, backoff_code + target)

# Apply backoff to add_data_to_sheet
if "@with_exponential_backoff(max_retries=3)\ndef add_data_to_sheet(sheet_name, row_dict):" not in content:
    content = content.replace("def add_data_to_sheet(sheet_name, row_dict):", "@with_exponential_backoff(max_retries=3)\ndef add_data_to_sheet(sheet_name, row_dict):")

# Apply to bulk points
if "@with_exponential_backoff(max_retries=3)\ndef bulk_award_points(updates_dict, reason=\"\"):" not in content:
    content = content.replace("def bulk_award_points(updates_dict, reason=\"\"):", "@with_exponential_backoff(max_retries=3)\ndef bulk_award_points(updates_dict, reason=\"\"):")


with open('app.py', 'w') as f:
    f.write(content)
