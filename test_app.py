import pytest
from app import app, mock_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.secret_key = 'test-secret'
    with app.test_client() as client:
        yield client

def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"ASWATHAMA CLASSES" in response.data

def test_unauthorized_api_access(client):
    # Should get 401 for api routes when not logged in
    response = client.get('/api/students')
    assert response.status_code == 401
    assert b"Unauthorized" in response.data

def test_unauthorized_view_access(client):
    # Should redirect to login for view routes when not logged in
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.location

def test_teacher_login_and_access(client):
    response = client.post('/api/login', json={
        "role": "teacher",
        "username": "admin",
        "password": "admin"
    })
    assert response.status_code == 200

    # Access dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Overview Dashboard" in response.data

    # Test getting students API
    response = client.get('/api/students')
    assert response.status_code == 200

    # Test logout
    client.post('/api/logout')
    response = client.get('/dashboard')
    assert response.status_code == 302

def test_student_login_and_access(client):
    # Student default login based on fallback logic in code
    response = client.post('/api/login', json={
        "role": "student",
        "roll_no": "student",
        "phone": "student"
    })
    assert response.status_code == 200

    # Access student dashboard
    response = client.get('/student_dashboard')
    assert response.status_code == 200
    assert b"Welcome" in response.data

    # Try accessing teacher route
    response = client.get('/dashboard')
    assert response.status_code == 302 # redirect because role != teacher

    # Check student API access (allowed to get attendance)
    response = client.get('/api/attendance')
    assert response.status_code == 200

def test_mock_db_structure():
    assert "students" in mock_db
    assert "attendance" in mock_db
    assert "videos" in mock_db
    assert "subjects" in mock_db
    assert "announcements" in mock_db
