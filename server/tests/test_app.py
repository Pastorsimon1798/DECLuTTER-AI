import io
import os
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from api.routes import analysis
from app.main import app
from security import dependencies

client = TestClient(app)

VALID_HEADERS = {
    'Authorization': 'Bearer test-user-token',
    'X-Firebase-AppCheck': 'test-app-check-token',
}


def _build_jpeg_with_exif() -> bytes:
    buffer = io.BytesIO()
    image = Image.new('RGB', (16, 16), color='green')
    image.save(buffer, format='JPEG', exif=b'Exif\x00\x00FAKE_EXIF_DATA')
    return buffer.getvalue()


def _set_auth_mode(mode: str) -> None:
    os.environ['DECLUTTER_AUTH_MODE'] = mode
    dependencies.get_firebase_verifier.cache_clear()


def test_health() -> None:
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_analysis_requires_auth_headers() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
    )
    assert response.status_code == 401


def test_analysis_scaffold() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=VALID_HEADERS,
    )
    body = response.json()
    assert response.status_code == 200
    assert body['session_id'] == 's-1'
    assert len(body['items']) >= 1
    assert body['engine'] == 'mock-structured-v1'
    assert body['structured_output_version'] == '2026-04-wp5-starter'


def test_intake_strips_exif_and_stores_file(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    analysis.intake_service.storage.base_dir = tmp_path

    payload = _build_jpeg_with_exif()
    response = client.post(
        '/analysis/intake',
        headers=VALID_HEADERS,
        files={'image': ('input.jpg', payload, 'image/jpeg')},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['storage_key'].startswith('intake/')
    assert body['content_type'] == 'image/jpeg'

    saved_path = tmp_path / body['storage_key']
    assert saved_path.exists()

    with Image.open(saved_path) as stored:
        assert not stored.getexif()


def test_strict_mode_returns_503_when_admin_sdk_not_configured() -> None:
    _set_auth_mode('strict')
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=VALID_HEADERS,
    )
    assert response.status_code == 503


def test_off_mode_allows_requests_without_headers() -> None:
    _set_auth_mode('off')
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
    )
    assert response.status_code == 200



def test_analysis_results_are_deterministic_for_key() -> None:
    _set_auth_mode('scaffold')
    payload = {'session_id': 's-1', 'image_storage_key': 'same/key.jpg'}

    first = client.post('/analysis/run', json=payload, headers=VALID_HEADERS)
    second = client.post('/analysis/run', json=payload, headers=VALID_HEADERS)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['items'] == second.json()['items']


def test_public_listing_does_not_require_auth() -> None:
    response = client.get('/public/listings/demo-listing')
    assert response.status_code == 200
    assert response.json()['listing_id'] == 'demo-listing'
