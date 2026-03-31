import re

with open('app.py', 'r') as f:
    content = f.read()

# I removed the def setup() function signature but left its body!
# Let's clean up any lingering setup route code completely.
start_idx = content.find("try:\n            success = init_google_sheet(gc, admin_email=admin_email)")
if start_idx != -1:
    end_idx = content.find("return render_template('login.html')", start_idx)
    if end_idx != -1:
        # this is a bit dangerous, let's just find the exact block and replace it
        pass

# The regex replacement missed the setup logic body:
body_to_remove = """
        try:
            success = init_google_sheet(gc, admin_email=admin_email)
            if success:
                global SPREADSHEET_ID
                sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
                flash(f"Successfully created and configured Google Sheet!<br><br>Shared with: {admin_email}<br><br><a href='{sheet_url}' target='_blank' style='color: #065f46; text-decoration: underline;'>Click Here to Open Your Google Sheet</a>", "success")
                app.config['db_initialized'] = True
            else:
                flash("Failed to create spreadsheet. Check server logs.", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

    return render_template('setup.html')"""

if body_to_remove in content:
    content = content.replace(body_to_remove, "")

# check if "if request.method == 'POST':" is orphaned
orphaned = """    if request.method == 'POST':
        admin_email = request.form.get('admin_email')
        gc = get_gspread_client()
        if not gc:
            flash("Failed to authenticate with Google. Check your credentials.json or GOOGLE_CREDENTIALS environment variable.", "error")"""
if orphaned in content:
    content = content.replace(orphaned, "")

# also the old attendance fallback loop body
orphaned_att = """        # Fallback to just mock db if sheets is down
        for record in records:
        return jsonify({'success': True})"""
if orphaned_att in content:
    content = content.replace(orphaned_att, "        return jsonify({'success': False, 'error': 'Cannot save: Sheet not found'})")

with open('app.py', 'w') as f:
    f.write(content)
