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



def test_intake_session_returns_signed_upload_stub() -> None:
    _set_auth_mode('scaffold')
    response = client.post('/analysis/intake/session', headers=VALID_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body['storage_key'].startswith('intake/')
    assert body['upload_url'].startswith('file://')
    assert body['expires_in_seconds'] > 0


def test_valuation_uses_comp_counts_and_source() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/valuation/estimate',
        headers=VALID_HEADERS,
        json={'label': 'electronics', 'condition': 'good'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['confidence'] in {'high', 'medium', 'low'}
    assert body['comp_count'] > 0
    assert body['source'] == 'mock-ebay-comps'
    assert body['estimated_high_usd'] >= body['estimated_low_usd']



def test_listing_draft_includes_checklist_and_category() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/listing-drafts/generate',
        headers=VALID_HEADERS,
        json={
            'item_label': 'electronics',
            'condition': 'good',
            'estimated_low_usd': 30.0,
            'estimated_high_usd': 50.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body['category_hint'] == 'Consumer Electronics'
    assert body['price_usd'] == 40.0
    assert len(body['review_checklist']) >= 3


def test_marketplace_publish_and_export_flow() -> None:
    _set_auth_mode('scaffold')
    payload = {
        'title': 'Vintage Camera - Good',
        'description': 'Clean body, tested shutter.',
        'condition': 'good',
        'price_usd': 89.0,
    }

    publish = client.post('/marketplace/ebay/publish', headers=VALID_HEADERS, json=payload)
    assert publish.status_code == 200
    publish_body = publish.json()
    assert publish_body['provider'] == 'ebay'
    assert publish_body['status'] == 'submitted_for_review'
    assert publish_body['listing_url'].startswith('https://www.ebay.com/itm/')

    export = client.post('/marketplace/ebay/export', headers=VALID_HEADERS, json=payload)
    assert export.status_code == 200
    export_body = export.json()
    assert export_body['format'] == 'csv'
    assert 'Vintage Camera - Good' in export_body['content']


def test_public_listing_does_not_require_auth() -> None:
    response = client.get('/public/listings/demo-listing')
    assert response.status_code == 200
    assert response.json()['listing_id'] == 'demo-listing'
