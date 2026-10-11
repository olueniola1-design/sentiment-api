import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_predict_endpoint(client):
    """Test that the API receives requests and returns a sentiment"""
    response = client.post('/predict', json={'tweet': 'I absolutely love this!'})
    assert response.status_code == 200, response.data
    json_data = response.get_json()
    assert 'sentiment' in json_data
    assert 'tweet' in json_data