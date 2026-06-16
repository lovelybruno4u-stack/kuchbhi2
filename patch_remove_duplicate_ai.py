with open('app.py', 'r') as f:
    content = f.read()

# Let's check why there are duplicates. Ah, I applied the patch_ai_endpoints.py twice? No, I appended it to the empty lines after # --- API Endpoints for AI Features (Teacher) --- and I did `content = content.replace("# --- API Endpoints for AI Features (Teacher) ---", "# --- API Endpoints for AI Features (Teacher) ---" + teacher_ai_endpoints)` multiple times maybe.
# Or maybe the file had two instances of `# --- API Endpoints for AI Features (Teacher) ---`? Let's check.
