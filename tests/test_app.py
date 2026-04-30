import pytest
from app import app, get_data, add_data_to_sheet

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    with app.test_client() as client:
        yield client

def test_index_redirects_to_login(client):
    rv = client.get('/')
    assert rv.status_code == 302
    assert '/login' in rv.location

def test_login_page_renders(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Ashwathama Classes - Login' in rv.data

def test_mock_db_fallback():
    # Attempting to add data should fall back to MOCK_DB if Google Sheets fails
    test_student = {'id': '123', 'name': 'John Doe', 'class': '10th', 'roll': '1', 'phone': '1234567890'}
    add_data_to_sheet('students', test_student)

    data = get_data('students')
    assert any(s.get('id') == '123' for s in data)

def test_api_unauthorized(client):
    rv = client.post('/api/ai/doubt', json={'question': 'what is python?'})
    assert rv.status_code == 401
