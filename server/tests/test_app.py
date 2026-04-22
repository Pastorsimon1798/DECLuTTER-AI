from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_HEADERS = {
    'Authorization': 'Bearer test-user-token',
    'X-Firebase-AppCheck': 'test-app-check-token',
}


def test_health() -> None:
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_analysis_requires_auth_headers() -> None:
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
    )
    assert response.status_code == 401


def test_analysis_scaffold() -> None:
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=VALID_HEADERS,
    )
    body = response.json()
    assert response.status_code == 200
    assert body['session_id'] == 's-1'
    assert len(body['items']) == 1


def test_public_listing_does_not_require_auth() -> None:
    response = client.get('/public/listings/demo-listing')
    assert response.status_code == 200
    assert response.json()['listing_id'] == 'demo-listing'
