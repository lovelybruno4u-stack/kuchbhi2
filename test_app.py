import pytest
from app import app, fallback_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.secret_key = 'test'
    with app.test_client() as client:
        yield client

def test_index_redirects_to_login(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Aswathama Classes' in response.data

def test_login_invalid_teacher(client):
    response = client.post('/login', json={'role': 'Teacher', 'username': 'wrong', 'password': '123'})
    assert response.status_code == 200
    assert response.json['success'] == False

def test_login_valid_teacher(client):
    response = client.post('/login', json={'role': 'Teacher', 'username': 'admin', 'password': 'admin'})
    assert response.status_code == 200
    assert response.json['success'] == True
    assert response.json['redirect'] == '/teacher/dashboard'
