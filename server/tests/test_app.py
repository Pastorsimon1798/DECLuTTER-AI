from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_analysis_scaffold() -> None:
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
    )
    body = response.json()
    assert response.status_code == 200
    assert body['session_id'] == 's-1'
    assert len(body['items']) == 1
