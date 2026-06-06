import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_page(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Ashwathama Classes' in rv.data
