kill $(lsof -t -i :5000) 2>/dev/null || true
export FLASK_APP=app.py
gunicorn app:app --bind 127.0.0.1:5000 > app.log 2>&1 &
