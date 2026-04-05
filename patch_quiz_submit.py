import re

with open('app.py', 'r') as f:
    content = f.read()

# Let's inspect the exact traceback by running it or simulating it.
# Wait, add_data_to_sheet('quiz_scores', score_record) might fail if the sheet doesn't have headers.
# ensure_worksheets does NOT add headers for quiz_scores properly unless defined in sheets_schema!
