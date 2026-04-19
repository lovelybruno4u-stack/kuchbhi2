import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_redirects_to_login(client):
    rv = client.get('/')
    assert rv.status_code == 302
    assert '/login' in rv.location
