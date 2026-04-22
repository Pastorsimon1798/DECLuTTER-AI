import io
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from api.routes import analysis
from app.main import app
from security import dependencies
from services.image_intake import ImageIntakeService
from services.storage_adapter import LocalImageStorageAdapter

client = TestClient(app)

VALID_HEADERS = {
    'Authorization': 'Bearer test-user-token',
    'X-Firebase-AppCheck': 'test-app-check-token',
}


def _clear_auth_env() -> None:
    for key in [
        'DECLUTTER_AUTH_MODE',
        'DECLUTTER_TEST_ID_TOKEN',
        'DECLUTTER_TEST_APP_CHECK_TOKEN',
    ]:
        os.environ.pop(key, None)
    dependencies.get_firebase_verifier.cache_clear()


def _clear_readiness_env() -> None:
    for key in [
        'FIREBASE_PROJECT_ID',
        'DECLUTTER_STORAGE_BACKEND',
        'DECLUTTER_S3_BUCKET',
        'DECLUTTER_STORAGE_BUCKET',
        'DECLUTTER_CORS_ALLOW_ORIGINS',
        'DECLUTTER_MODEL_PROVIDER',
        'EBAY_CLIENT_ID',
        'EBAY_CLIENT_SECRET',
    ]:
        os.environ.pop(key, None)


def _build_jpeg_with_exif() -> bytes:
    buffer = io.BytesIO()
    image = Image.new('RGB', (16, 16), color='green')
    image.save(buffer, format='JPEG', exif=b'Exif\x00\x00FAKE_EXIF_DATA')
    return buffer.getvalue()


def _set_auth_mode(mode: str) -> None:
    os.environ['DECLUTTER_AUTH_MODE'] = mode
    if mode == 'scaffold':
        os.environ['DECLUTTER_TEST_ID_TOKEN'] = 'test-user-token'
        os.environ['DECLUTTER_TEST_APP_CHECK_TOKEN'] = 'test-app-check-token'
    dependencies.get_firebase_verifier.cache_clear()


def test_health() -> None:
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_root_landing_page_links_launch_surfaces() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert 'DECLuTTER-AI' in response.text
    assert '/docs' in response.text
    assert '/health/readiness' in response.text


def test_launch_status_reports_backend_scaffold_limitations() -> None:
    _clear_readiness_env()
    response = client.get('/launch/status')
    assert response.status_code == 200
    body = response.json()
    assert body['service'] == 'DECLuTTER-AI API'
    assert body['launch_profile'] == 'backend_scaffold'
    assert body['checks']['firebase_admin_configured'] is False
    assert body['checks']['cloud_storage_configured'] is False
    assert body['checks']['multimodal_model_configured'] is False
    assert body['checks']['ebay_api_configured'] is False
    assert body['production_ready'] == all(body['checks'].values())
    assert 'deterministic starter adapters' in ' '.join(body['limitations'])



def test_readiness_defaults_to_not_ready() -> None:
    _clear_readiness_env()

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['ready_for_production'] is False


def test_readiness_can_report_ready_when_all_env_present() -> None:
    os.environ['FIREBASE_PROJECT_ID'] = 'demo-project'
    os.environ['DECLUTTER_STORAGE_BACKEND'] = 's3'
    os.environ['DECLUTTER_S3_BUCKET'] = 'bucket'
    os.environ.pop('DECLUTTER_STORAGE_BUCKET', None)
    os.environ['DECLUTTER_MODEL_PROVIDER'] = 'mock-model'
    os.environ['EBAY_CLIENT_ID'] = 'id'
    os.environ['EBAY_CLIENT_SECRET'] = 'secret'

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['ready_for_production'] is True


def test_readiness_ignores_legacy_storage_bucket_without_s3_config() -> None:
    os.environ['FIREBASE_PROJECT_ID'] = 'demo-project'
    os.environ.pop('DECLUTTER_STORAGE_BACKEND', None)
    os.environ.pop('DECLUTTER_S3_BUCKET', None)
    os.environ['DECLUTTER_STORAGE_BUCKET'] = 'legacy-bucket'
    os.environ['DECLUTTER_MODEL_PROVIDER'] = 'mock-model'
    os.environ['EBAY_CLIENT_ID'] = 'id'
    os.environ['EBAY_CLIENT_SECRET'] = 'secret'

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['ready_for_production'] is False


def test_configured_cors_origin_allows_preflight(monkeypatch) -> None:
    monkeypatch.setenv('DECLUTTER_CORS_ALLOW_ORIGINS', 'https://app.declutter.ai')
    from app.main import create_app

    cors_client = TestClient(create_app())
    response = cors_client.options(
        '/analysis/run',
        headers={
            'Origin': 'https://app.declutter.ai',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'authorization,x-firebase-appcheck',
        },
    )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://app.declutter.ai'


def test_s3_misconfiguration_does_not_block_app_import(tmp_path: Path) -> None:
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'app')
    env['DECLUTTER_STORAGE_BACKEND'] = 's3'
    env.pop('DECLUTTER_S3_BUCKET', None)

    result = subprocess.run(
        [sys.executable, '-c', 'import app.main; print("imported")'],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert 'imported' in result.stdout


def test_analysis_requires_auth_headers() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
    )
    assert response.status_code == 401


def test_default_auth_mode_does_not_accept_scaffold_tokens() -> None:
    _clear_auth_env()
    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=VALID_HEADERS,
    )
    assert response.status_code == 503
    assert (
        response.json()['detail']
        == 'Strict auth mode requires firebase-admin to be installed.'
    )


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
    app.dependency_overrides[analysis.get_image_intake_service] = lambda: ImageIntakeService(
        storage=LocalImageStorageAdapter(str(tmp_path))
    )

    try:
        payload = _build_jpeg_with_exif()
        response = client.post(
            '/analysis/intake',
            headers=VALID_HEADERS,
            files={'image': ('input.jpg', payload, 'image/jpeg')},
        )
    finally:
        app.dependency_overrides.pop(analysis.get_image_intake_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body['storage_key'].startswith('intake/')
    assert body['content_type'] == 'image/jpeg'

    saved_path = tmp_path / body['storage_key']
    assert saved_path.exists()

    with Image.open(saved_path) as stored:
        assert not stored.getexif()


def test_intake_returns_400_for_malformed_image_bytes() -> None:
    _set_auth_mode('scaffold')
    response = client.post(
        '/analysis/intake',
        headers=VALID_HEADERS,
        files={'image': ('not-really.jpg', b'not an image', 'image/jpeg')},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Malformed or unreadable image upload.'


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


def test_public_listing_unknown_id_does_not_require_auth() -> None:
    response = client.get('/public/listings/demo-listing')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Public listing not found.'





def test_cash_to_clear_session_create_accepts_empty_body(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions

    sessions.get_cash_to_clear_service.cache_clear()

    response = client.post('/sessions', headers=VALID_HEADERS)

    assert response.status_code == 200
    assert response.json()['session_id'].startswith('sess_')


def test_cash_to_clear_sessions_are_scoped_to_authenticated_user(tmp_path: Path) -> None:
    from types import SimpleNamespace

    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions

    class TokenUidVerifier:
        settings = SimpleNamespace(auth_mode='strict')

        def verify_id_token(self, token: str) -> dict[str, str]:
            return {'uid': token}

        def verify_app_check_token(self, token: str) -> dict[str, str]:
            return {'app_id': token}

    sessions.get_cash_to_clear_service.cache_clear()
    dependencies.get_firebase_verifier.cache_clear()
    app.dependency_overrides[dependencies.get_firebase_verifier] = TokenUidVerifier

    try:
        alice_headers = {
            'Authorization': 'Bearer alice',
            'X-Firebase-AppCheck': 'test-app-check-token',
        }
        bob_headers = {
            'Authorization': 'Bearer bob',
            'X-Firebase-AppCheck': 'test-app-check-token',
        }
        create = client.post('/sessions', headers=alice_headers)
        assert create.status_code == 200
        session_id = create.json()['session_id']

        bob_read = client.get(f'/sessions/{session_id}', headers=bob_headers)
        assert bob_read.status_code == 404
        assert bob_read.json()['detail'] == 'Session not found.'

        bob_add_item = client.post(
            f'/sessions/{session_id}/items',
            headers=bob_headers,
            json={'label': 'electronics', 'condition': 'good'},
        )
        assert bob_add_item.status_code == 404

        alice_read = client.get(f'/sessions/{session_id}', headers=alice_headers)
        assert alice_read.status_code == 200
        assert alice_read.json()['session_id'] == session_id
    finally:
        app.dependency_overrides.pop(dependencies.get_firebase_verifier, None)
        dependencies.get_firebase_verifier.cache_clear()

def test_cash_to_clear_sessions_require_auth() -> None:
    _set_auth_mode('scaffold')
    response = client.post('/sessions', json={})
    assert response.status_code == 401

def test_cash_to_clear_session_persists_items_decisions_and_totals(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions

    sessions.get_cash_to_clear_service.cache_clear()

    create = client.post(
        '/sessions',
        headers=VALID_HEADERS,
        json={'image_storage_key': 'intake/demo.jpg'},
    )
    assert create.status_code == 200
    created = create.json()
    assert created['image_storage_key'] == 'intake/demo.jpg'
    assert created['money_on_table_low_usd'] == 0

    add_item = client.post(
        f"/sessions/{created['session_id']}/items",
        headers=VALID_HEADERS,
        json={'label': 'electronics', 'condition': 'good'},
    )
    assert add_item.status_code == 200
    item = add_item.json()
    assert item['label'] == 'electronics'
    assert item['valuation']['estimated_low_usd'] > 0
    assert item['listing_draft']['title'] == 'Electronics - Good'

    after_item = client.get(f"/sessions/{created['session_id']}", headers=VALID_HEADERS)
    assert after_item.status_code == 200
    body = after_item.json()
    assert len(body['items']) == 1
    assert body['money_on_table_low_usd'] == item['valuation']['estimated_low_usd']
    assert body['items'][0]['decision'] is None

    decision = client.post(
        f"/sessions/{created['session_id']}/decisions",
        headers=VALID_HEADERS,
        json={'item_id': item['item_id'], 'decision': 'donate', 'note': 'Not worth listing today'},
    )
    assert decision.status_code == 200
    decided = decision.json()
    assert decided['decision'] == 'donate'
    assert decided['note'] == 'Not worth listing today'

    after_decision = client.get(f"/sessions/{created['session_id']}", headers=VALID_HEADERS)
    assert after_decision.status_code == 200
    final_body = after_decision.json()
    assert final_body['money_on_table_low_usd'] == 0
    assert final_body['items'][0]['decision']['decision'] == 'donate'



def test_cash_to_clear_maybe_decision_removes_item_from_money_total(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions

    sessions.get_cash_to_clear_service.cache_clear()

    create = client.post('/sessions', headers=VALID_HEADERS, json={})
    assert create.status_code == 200
    session_id = create.json()['session_id']

    add_item = client.post(
        f'/sessions/{session_id}/items',
        headers=VALID_HEADERS,
        json={'label': 'electronics', 'condition': 'good'},
    )
    assert add_item.status_code == 200
    item = add_item.json()
    assert item['valuation']['estimated_low_usd'] > 0

    decision = client.post(
        f'/sessions/{session_id}/decisions',
        headers=VALID_HEADERS,
        json={'item_id': item['item_id'], 'decision': 'maybe'},
    )
    assert decision.status_code == 200

    after_decision = client.get(f'/sessions/{session_id}', headers=VALID_HEADERS)
    assert after_decision.status_code == 200
    assert after_decision.json()['money_on_table_low_usd'] == 0

def test_cash_to_clear_rejects_decision_for_unknown_item(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions

    sessions.get_cash_to_clear_service.cache_clear()

    create = client.post('/sessions', headers=VALID_HEADERS, json={})
    assert create.status_code == 200
    session_id = create.json()['session_id']

    response = client.post(
        f'/sessions/{session_id}/decisions',
        headers=VALID_HEADERS,
        json={'item_id': 'missing', 'decision': 'sell'},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Item not found for this session.'


def test_cash_to_clear_can_publish_standalone_html_listing_page(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions
    from api.routes import public_listings

    sessions.get_cash_to_clear_service.cache_clear()
    public_listings.get_public_listing_service.cache_clear()

    create = client.post('/sessions', headers=VALID_HEADERS, json={})
    assert create.status_code == 200
    session_id = create.json()['session_id']

    add_item = client.post(
        f'/sessions/{session_id}/items',
        headers=VALID_HEADERS,
        json={'label': 'electronics', 'condition': 'good'},
    )
    assert add_item.status_code == 200
    item = add_item.json()

    publish = client.post(
        f"/sessions/{session_id}/items/{item['item_id']}/public-listing",
        headers=VALID_HEADERS,
    )
    assert publish.status_code == 200
    public_listing = publish.json()
    assert public_listing['listing_id'].startswith('pub_')
    assert public_listing['public_url'] == f"/public/listings/{public_listing['listing_id']}"
    assert public_listing['title'] == item['listing_draft']['title']

    html = client.get(public_listing['public_url'])
    assert html.status_code == 200
    assert html.headers['content-type'].startswith('text/html')
    assert 'Electronics - Good' in html.text
    assert 'Consumer Electronics' in html.text
    assert '<script' not in html.text.lower()

    packet = client.get(f"/public/listings/{public_listing['listing_id']}/packet")
    assert packet.status_code == 200
    assert packet.json()['listing_id'] == public_listing['listing_id']
    assert packet.json()['price_usd'] == item['listing_draft']['price_usd']


def test_public_listing_unknown_id_returns_404() -> None:
    response = client.get('/public/listings/pub_missing')
    assert response.status_code == 404
