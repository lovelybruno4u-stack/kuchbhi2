import pytest
from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_login_and_routing(client):
    # Test teacher login
    rv = client.post('/login', data={'role': 'teacher', 'password': 'admin123'}, follow_redirects=True)
    assert b'teacher/dashboard.html' in rv.data or rv.status_code == 200 # If templates exist

    # Check access to protected teacher route
    rv = client.get('/teacher/students')
    assert rv.status_code == 200

    # Logout
    client.get('/logout')

@patch('app.client.chat.completions.create')
def test_ai_announcement(mock_create, client):
    # Mock OpenAI response
    mock_create.return_value.choices = [
        type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mocked announcement'})})
    ]

    # Login as teacher first
    with client.session_transaction() as sess:
        sess['role'] = 'teacher'
        sess['user_id'] = 'admin'

    rv = client.post('/api/ai/announcement', json={'topic': 'Holiday'})
    assert rv.status_code == 200
    assert rv.json['result'] == 'Mocked announcement'

@patch('app.client.chat.completions.create')
def test_ai_doubt_solver(mock_create, client):
    # Mock OpenAI response
    mock_create.return_value.choices = [
        type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mocked solution'})})
    ]

    # Login as student first
    with client.session_transaction() as sess:
        sess['role'] = 'student'
        sess['user_id'] = '123'

    rv = client.post('/api/ai/doubt_solver', json={'question': 'What is gravity?'})
    assert rv.status_code == 200
    assert rv.json['result'] == 'Mocked solution'
