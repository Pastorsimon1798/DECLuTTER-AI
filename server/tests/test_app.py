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
from services.analysis_adapter import OpenAICompatibleAnalysisAdapter
from services.image_intake import ImageIntakeService
from services.storage_adapter import LocalImageStorageAdapter

client = TestClient(app)

VALID_HEADERS = {
    'Authorization': 'Bearer test-user-token',
    'X-Firebase-AppCheck': 'test-app-check-token',
}

SHARED_TOKEN_HEADERS = {
    'Authorization': 'Bearer self-hosted-secret',
}


def _clear_auth_env() -> None:
    for key in [
        'DECLUTTER_AUTH_MODE',
        'DECLUTTER_SHARED_ACCESS_TOKEN',
        'DECLUTTER_TEST_ID_TOKEN',
        'DECLUTTER_TEST_APP_CHECK_TOKEN',
    ]:
        os.environ.pop(key, None)
    dependencies.get_firebase_verifier.cache_clear()
    analysis.get_analysis_adapter.cache_clear()


def _clear_readiness_env() -> None:
    for key in [
        'FIREBASE_PROJECT_ID',
        'DECLUTTER_STORAGE_BACKEND',
        'DECLUTTER_S3_BUCKET',
        'DECLUTTER_STORAGE_BUCKET',
        'DECLUTTER_CORS_ALLOW_ORIGINS',
        'DECLUTTER_MODEL_PROVIDER',
        'DECLUTTER_ANALYSIS_PROVIDER',
        'DECLUTTER_INFERENCE_API_KEY',
        'DECLUTTER_INFERENCE_BASE_URL',
        'DECLUTTER_INFERENCE_MODEL',
        'DECLUTTER_INFERENCE_TIMEOUT_SECONDS',
        'OPENAI_BASE_URL',
        'OPENAI_MODEL',
        'LMSTUDIO_BASE_URL',
        'LMSTUDIO_MODEL',
        'LM_STUDIO_BASE_URL',
        'LM_STUDIO_MODEL',
        'DECLUTTER_AUTH_MODE',
        'DECLUTTER_SHARED_ACCESS_TOKEN',
        'DECLUTTER_UPLOAD_DIR',
        'DECLUTTER_SESSION_DB_PATH',
        'EBAY_CLIENT_ID',
        'EBAY_CLIENT_SECRET',
    ]:
        os.environ.pop(key, None)
    analysis.get_analysis_adapter.cache_clear()


def _build_jpeg_with_exif() -> bytes:
    buffer = io.BytesIO()
    image = Image.new('RGB', (16, 16), color='green')
    image.save(buffer, format='JPEG', exif=b'Exif\x00\x00FAKE_EXIF_DATA')
    return buffer.getvalue()


def _clear_analysis_env() -> None:
    for key in [
        'DECLUTTER_ANALYSIS_PROVIDER',
        'DECLUTTER_INFERENCE_API_KEY',
        'DECLUTTER_INFERENCE_BASE_URL',
        'DECLUTTER_INFERENCE_MODEL',
        'DECLUTTER_INFERENCE_TIMEOUT_SECONDS',
        'OPENAI_BASE_URL',
        'OPENAI_MODEL',
        'LMSTUDIO_BASE_URL',
        'LMSTUDIO_MODEL',
        'LM_STUDIO_BASE_URL',
        'LM_STUDIO_MODEL',
    ]:
        os.environ.pop(key, None)
    analysis.get_analysis_adapter.cache_clear()


def _set_auth_mode(mode: str) -> None:
    _clear_analysis_env()
    os.environ['DECLUTTER_AUTH_MODE'] = mode
    if mode == 'scaffold':
        os.environ['DECLUTTER_TEST_ID_TOKEN'] = 'test-user-token'
        os.environ['DECLUTTER_TEST_APP_CHECK_TOKEN'] = 'test-app-check-token'
    dependencies.get_firebase_verifier.cache_clear()
    analysis.get_analysis_adapter.cache_clear()


def test_health() -> None:
    response = client.get('/health/')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_root_landing_page_links_launch_surfaces() -> None:
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert 'DECLuTTER-AI' in response.text
    assert 'One photo. One sprint. One less pile.' in response.text
    assert '/app' in response.text
    assert '/health/readiness' in response.text


def test_launch_status_reports_backend_scaffold_limitations() -> None:
    _clear_readiness_env()
    response = client.get('/launch/status')
    assert response.status_code == 200
    body = response.json()
    assert body['service'] == 'DECLuTTER-AI API'
    assert body['launch_profile'] == 'seller_front_door_beta'
    assert body['self_hosted_mvp_ready'] is False
    assert body['checks']['firebase_admin_configured'] is False
    assert body['checks']['cloud_storage_configured'] is False
    assert body['checks']['multimodal_model_configured'] is False
    assert body['checks']['ebay_api_configured'] is False
    assert body['production_ready'] == all(body['checks'].values())
    assert 'promotable front door' in ' '.join(body['limitations'])



def test_readiness_defaults_to_not_ready() -> None:
    _clear_readiness_env()

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['self_hosted_mvp_ready'] is False
    assert body['ready_for_production'] is False


def test_readiness_can_report_self_hosted_mvp_ready(tmp_path: Path) -> None:
    _clear_readiness_env()
    os.environ['DECLUTTER_AUTH_MODE'] = 'shared_token'
    os.environ['DECLUTTER_SHARED_ACCESS_TOKEN'] = 'self-hosted-secret'
    os.environ['DECLUTTER_STORAGE_BACKEND'] = 'local'
    os.environ['DECLUTTER_UPLOAD_DIR'] = str(tmp_path / 'uploads')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['self_hosted_mvp_ready'] is True
    assert body['ready_for_production'] is False
    assert body['checks']['shared_token_auth_configured'] is True
    assert body['checks']['local_upload_storage_configured'] is True
    assert body['checks']['sqlite_session_store_configured'] is True


def test_readiness_reports_home_inference_when_openai_compatible_env_present(
    tmp_path: Path,
) -> None:
    _clear_readiness_env()
    os.environ['DECLUTTER_AUTH_MODE'] = 'shared_token'
    os.environ['DECLUTTER_SHARED_ACCESS_TOKEN'] = 'self-hosted-secret'
    os.environ['DECLUTTER_STORAGE_BACKEND'] = 'local'
    os.environ['DECLUTTER_UPLOAD_DIR'] = str(tmp_path / 'uploads')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    os.environ['DECLUTTER_ANALYSIS_PROVIDER'] = 'lmstudio'
    os.environ['LMSTUDIO_BASE_URL'] = 'http://host.docker.internal:1234/v1'
    os.environ['LMSTUDIO_MODEL'] = 'qwen-vision-local'

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['self_hosted_mvp_ready'] is True
    assert body['checks']['home_inference_configured'] is True
    assert body['checks']['multimodal_model_configured'] is True


def test_readiness_can_report_ready_when_all_env_present() -> None:
    os.environ['FIREBASE_PROJECT_ID'] = 'declutter-prod-123'
    os.environ['DECLUTTER_STORAGE_BACKEND'] = 's3'
    os.environ['DECLUTTER_S3_BUCKET'] = 'declutter-prod-uploads'
    os.environ.pop('DECLUTTER_STORAGE_BUCKET', None)
    os.environ['DECLUTTER_MODEL_PROVIDER'] = 'openai-gpt-5-4'
    os.environ['EBAY_CLIENT_ID'] = 'declutter-ebay-client-123'
    os.environ['EBAY_CLIENT_SECRET'] = 'prod-ebay-secret-abc123'

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['ready_for_production'] is True


def test_readiness_rejects_env_example_placeholders() -> None:
    _clear_readiness_env()
    os.environ['FIREBASE_PROJECT_ID'] = 'your-firebase-project-id'
    os.environ['DECLUTTER_STORAGE_BACKEND'] = 's3'
    os.environ['DECLUTTER_S3_BUCKET'] = 'your-private-upload-bucket'
    os.environ['DECLUTTER_MODEL_PROVIDER'] = 'launch-model-provider'
    os.environ['EBAY_CLIENT_ID'] = 'your-ebay-client-id'
    os.environ['EBAY_CLIENT_SECRET'] = 'your-ebay-client-secret'

    response = client.get('/health/readiness')
    assert response.status_code == 200
    body = response.json()
    assert body['ready_for_production'] is False
    assert body['checks']['firebase_admin_configured'] is False
    assert body['checks']['cloud_storage_configured'] is False
    assert body['checks']['multimodal_model_configured'] is False
    assert body['checks']['ebay_api_configured'] is False


def test_readiness_ignores_legacy_storage_bucket_without_s3_config() -> None:
    os.environ['FIREBASE_PROJECT_ID'] = 'declutter-prod-123'
    os.environ.pop('DECLUTTER_STORAGE_BACKEND', None)
    os.environ.pop('DECLUTTER_S3_BUCKET', None)
    os.environ['DECLUTTER_STORAGE_BUCKET'] = 'legacy-bucket'
    os.environ['DECLUTTER_MODEL_PROVIDER'] = 'openai-gpt-5-4'
    os.environ['EBAY_CLIENT_ID'] = 'declutter-ebay-client-123'
    os.environ['EBAY_CLIENT_SECRET'] = 'prod-ebay-secret-abc123'

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
        == 'Authentication service temporarily unavailable. Please try again later.'
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


def test_analysis_accepts_self_hosted_shared_token_without_app_check() -> None:
    os.environ['DECLUTTER_AUTH_MODE'] = 'shared_token'
    os.environ['DECLUTTER_SHARED_ACCESS_TOKEN'] = 'self-hosted-secret'
    dependencies.get_firebase_verifier.cache_clear()

    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=SHARED_TOKEN_HEADERS,
    )
    body = response.json()
    assert response.status_code == 200
    assert body['session_id'] == 's-1'
    assert len(body['items']) >= 1


def test_analysis_rejects_wrong_self_hosted_shared_token() -> None:
    os.environ['DECLUTTER_AUTH_MODE'] = 'shared_token'
    os.environ['DECLUTTER_SHARED_ACCESS_TOKEN'] = 'self-hosted-secret'
    dependencies.get_firebase_verifier.cache_clear()

    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers={'Authorization': 'Bearer wrong-token'},
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Authentication failed. Please check your credentials and try again.'


def test_bad_home_inference_config_does_not_break_health() -> None:
    _clear_readiness_env()
    os.environ['DECLUTTER_ANALYSIS_PROVIDER'] = 'lmstudio'
    os.environ.pop('DECLUTTER_INFERENCE_MODEL', None)
    os.environ.pop('LMSTUDIO_MODEL', None)
    analysis.get_analysis_adapter.cache_clear()

    response = client.get('/health/readiness')

    assert response.status_code == 200
    body = response.json()
    assert body['checks']['home_inference_configured'] is False


def test_bad_home_inference_config_returns_controlled_503() -> None:
    _set_auth_mode('shared_token')
    os.environ['DECLUTTER_SHARED_ACCESS_TOKEN'] = 'self-hosted-secret'
    os.environ['DECLUTTER_ANALYSIS_PROVIDER'] = 'lmstudio'
    os.environ.pop('DECLUTTER_INFERENCE_MODEL', None)
    os.environ.pop('LMSTUDIO_MODEL', None)
    analysis.get_analysis_adapter.cache_clear()

    response = client.post(
        '/analysis/run',
        json={'session_id': 's-1', 'image_storage_key': 'private/key.jpg'},
        headers=SHARED_TOKEN_HEADERS,
    )

    assert response.status_code == 503
    assert 'required for OpenAI-compatible analysis' in response.json()['detail']


def test_openai_compatible_analysis_adapter_parses_structured_items(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / 'intake' / 'item.jpg'
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(_build_jpeg_with_exif())
    calls: list[dict[str, object]] = []

    def fake_transport(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> dict[str, object]:
        calls.append(
            {
                'url': url,
                'payload': payload,
                'headers': headers,
                'timeout_seconds': timeout_seconds,
            }
        )
        return {
            'choices': [
                {
                    'message': {
                        'content': (
                            '{"items":[{"label":"camera", "confidence":0.91}, '
                            '{"label":"box", "confidence":1.4}]}'
                        )
                    }
                }
            ]
        }

    adapter = OpenAICompatibleAnalysisAdapter(
        base_url='http://host.docker.internal:1234/v1',
        model='local-vision-model',
        api_key='local-key',
        upload_dir=str(tmp_path),
        timeout_seconds=12,
        transport=fake_transport,
    )

    result = adapter.run('intake/item.jpg')

    assert result.engine == 'openai-compatible:local-vision-model'
    assert result.structured_output_version == '2026-04-home-inference'
    assert [item.label for item in result.items] == ['camera', 'box']
    assert result.items[1].confidence == 1.0
    assert calls[0]['url'] == 'http://host.docker.internal:1234/v1/chat/completions'
    assert calls[0]['headers'] == {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer local-key',
    }
    request_payload = calls[0]['payload']
    assert isinstance(request_payload, dict)
    assert request_payload['model'] == 'local-vision-model'
    assert request_payload['max_tokens'] == 256
    assert request_payload['response_format'] == {'type': 'text'}
    user_content = request_payload['messages'][1]['content']  # type: ignore[index]
    assert user_content[1]['image_url']['url'].startswith('data:image/jpeg;base64,')



def test_openai_compatible_analysis_adapter_parses_fenced_json() -> None:
    adapter = OpenAICompatibleAnalysisAdapter(
        base_url='http://host.docker.internal:1234/v1',
        model='local-vision-model',
        transport=lambda _url, _payload, _headers, _timeout: {
            'choices': [
                {
                    'message': {
                        'content': '```json\n{"items":[{"label":"blue book","confidence":0.9}]}\n```'
                    }
                }
            ]
        },
    )

    result = adapter.run('intake/missing.jpg')

    assert result.items[0].label == 'blue book'
    assert result.items[0].confidence == 0.9


def test_openai_compatible_analysis_adapter_retries_with_fallback_prompt() -> None:
    calls: list[dict[str, object]] = []

    def flaky_transport(
        _url: str,
        payload: dict[str, object],
        _headers: dict[str, str],
        _timeout: float,
    ) -> dict[str, object]:
        calls.append(payload)
        if len(calls) == 1:
            return {'choices': [{'message': {'content': ''}}]}
        return {
            'choices': [
                {
                    'message': {
                        'content': '```json\n{"items":[{"label":"camera","confidence":0.88}]}\n```'
                    }
                }
            ]
        }

    adapter = OpenAICompatibleAnalysisAdapter(
        base_url='http://host.docker.internal:1234/v1',
        model='local-vision-model',
        transport=flaky_transport,
    )

    result = adapter.run('intake/missing.jpg')

    assert result.items[0].label == 'camera'
    assert len(calls) == 2
    first_messages = calls[0]['messages']  # type: ignore[index]
    second_messages = calls[1]['messages']  # type: ignore[index]
    assert first_messages[0]['content'].endswith('Do not include markdown.')
    assert 'Identify the visible items in this image' in second_messages[1]['content'][0]['text']


def test_openai_compatible_analysis_adapter_rejects_empty_choices() -> None:
    adapter = OpenAICompatibleAnalysisAdapter(
        base_url='http://host.docker.internal:1234/v1',
        model='local-vision-model',
        transport=lambda _url, _payload, _headers, _timeout: {'choices': []},
    )

    try:
        adapter.run('intake/missing.jpg')
    except RuntimeError as exc:
        assert str(exc) == 'Inference provider returned no choices.'
    else:
        raise AssertionError('empty choices should raise RuntimeError')


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
    assert public_listing['public_url'] == f"/listings/{public_listing['listing_id']}"
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


def test_cash_to_clear_session_summary_includes_counts_totals_and_listing_links(tmp_path: Path) -> None:
    _set_auth_mode('scaffold')
    os.environ['DECLUTTER_SESSION_DB_PATH'] = str(tmp_path / 'sessions.sqlite3')
    from api.routes import sessions
    from api.routes import public_listings

    sessions.get_cash_to_clear_service.cache_clear()
    public_listings.get_public_listing_service.cache_clear()

    create = client.post('/sessions', headers=VALID_HEADERS, json={})
    assert create.status_code == 200
    session_id = create.json()['session_id']

    item_one = client.post(
        f'/sessions/{session_id}/items',
        headers=VALID_HEADERS,
        json={'label': 'electronics', 'condition': 'good'},
    ).json()
    item_two = client.post(
        f'/sessions/{session_id}/items',
        headers=VALID_HEADERS,
        json={'label': 'book', 'condition': 'fair'},
    ).json()

    client.post(
        f'/sessions/{session_id}/decisions',
        headers=VALID_HEADERS,
        json={'item_id': item_one['item_id'], 'decision': 'sell'},
    )
    client.post(
        f'/sessions/{session_id}/decisions',
        headers=VALID_HEADERS,
        json={'item_id': item_two['item_id'], 'decision': 'donate'},
    )
    public_listing = client.post(
        f"/sessions/{session_id}/items/{item_one['item_id']}/public-listing",
        headers=VALID_HEADERS,
    ).json()

    summary = client.get(f'/sessions/{session_id}/summary', headers=VALID_HEADERS)

    assert summary.status_code == 200
    body = summary.json()
    assert body['session_id'] == session_id
    assert body['total_items'] == 2
    assert body['decided_items'] == 2
    assert body['decision_counts']['sell'] == 1
    assert body['decision_counts']['donate'] == 1
    assert body['money_on_table_low_usd'] == item_one['valuation']['estimated_low_usd']
    assert body['total_estimated_low_usd'] == item_one['valuation']['estimated_low_usd'] + item_two['valuation']['estimated_low_usd']
    assert body['public_listings'][0]['listing_id'] == public_listing['listing_id']
    assert body['public_listings'][0]['item_id'] == item_one['item_id']


def test_cash_to_clear_session_history_lists_only_authenticated_user_sessions(tmp_path: Path) -> None:
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
        alice_session = client.post('/sessions', headers=alice_headers).json()
        bob_session = client.post('/sessions', headers=bob_headers).json()

        alice_item = client.post(
            f"/sessions/{alice_session['session_id']}/items",
            headers=alice_headers,
            json={'label': 'electronics', 'condition': 'good'},
        ).json()
        client.post(
            f"/sessions/{alice_session['session_id']}/decisions",
            headers=alice_headers,
            json={'item_id': alice_item['item_id'], 'decision': 'sell'},
        )

        alice_history = client.get('/sessions', headers=alice_headers)
        bob_history = client.get('/sessions', headers=bob_headers)

        assert alice_history.status_code == 200
        assert bob_history.status_code == 200
        assert [entry['session_id'] for entry in alice_history.json()['sessions']] == [alice_session['session_id']]
        assert [entry['session_id'] for entry in bob_history.json()['sessions']] == [bob_session['session_id']]
        assert alice_history.json()['sessions'][0]['total_items'] == 1
        assert alice_history.json()['sessions'][0]['decided_items'] == 1
    finally:
        app.dependency_overrides.pop(dependencies.get_firebase_verifier, None)
        dependencies.get_firebase_verifier.cache_clear()



def test_operator_requires_basic_auth(monkeypatch) -> None:
    monkeypatch.setenv('DECLUTTER_SHARED_ACCESS_TOKEN', 'operator-secret')
    response = client.get('/operator')

    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Basic realm="DECLuTTER-AI Operator"'


def test_operator_home_renders_private_form(monkeypatch) -> None:
    monkeypatch.setenv('DECLUTTER_SHARED_ACCESS_TOKEN', 'operator-secret')
    response = client.get('/operator', auth=('operator', 'operator-secret'))

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert 'Run Cash-to-Clear sprint' in response.text
    assert 'DECLuTTER-AI Operator' in response.text


def test_operator_sprint_runs_without_exposing_bearer_token(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from api.routes import operator, public_listings

    monkeypatch.setenv('DECLUTTER_SHARED_ACCESS_TOKEN', 'operator-secret')
    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 'local')
    monkeypatch.setenv('DECLUTTER_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('DECLUTTER_SESSION_DB_PATH', str(tmp_path / 'sessions.sqlite3'))
    monkeypatch.setenv('DECLUTTER_ANALYSIS_PROVIDER', 'mock')
    monkeypatch.setenv('DECLUTTER_PUBLIC_BASE_PATH', 'declutter')
    operator.get_operator_image_intake_service.cache_clear()
    operator.get_operator_analysis_adapter.cache_clear()
    operator.get_operator_session_store.cache_clear()
    public_listings.get_public_listing_service.cache_clear()

    try:
        response = client.post(
            '/operator/sprint',
            auth=('operator', 'operator-secret'),
            data={'condition': 'good', 'label_override': 'camera'},
            files={'image': ('input.jpg', _build_jpeg_with_exif(), 'image/jpeg')},
            headers={'host': 'kyanitelabs.tech', 'x-forwarded-proto': 'https'},
        )

        assert response.status_code == 200
        assert 'Sprint complete' in response.text
        assert 'Camera' in response.text or 'camera' in response.text
        assert 'https://kyanitelabs.tech/declutter/listings/' in response.text
        assert 'operator-secret' not in response.text
    finally:
        operator.get_operator_image_intake_service.cache_clear()
        if hasattr(operator.get_operator_analysis_adapter, 'cache_clear'):
            operator.get_operator_analysis_adapter.cache_clear()
        operator.get_operator_session_store.cache_clear()
        public_listings.get_public_listing_service.cache_clear()


def test_operator_sprint_uses_manual_label_when_inference_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from api.routes import operator, public_listings

    class FailingAdapter:
        def run(self, image_storage_key: str):
            raise RuntimeError('model is temporarily unavailable')

    monkeypatch.setenv('DECLUTTER_SHARED_ACCESS_TOKEN', 'operator-secret')
    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 'local')
    monkeypatch.setenv('DECLUTTER_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('DECLUTTER_SESSION_DB_PATH', str(tmp_path / 'sessions.sqlite3'))
    monkeypatch.setenv('DECLUTTER_PUBLIC_BASE_PATH', 'declutter')
    operator.get_operator_image_intake_service.cache_clear()
    operator.get_operator_analysis_adapter.cache_clear()
    operator.get_operator_session_store.cache_clear()
    public_listings.get_public_listing_service.cache_clear()
    monkeypatch.setattr(operator, 'get_operator_analysis_adapter', lambda: FailingAdapter())

    try:
        response = client.post(
            '/operator/sprint',
            auth=('operator', 'operator-secret'),
            data={'condition': 'good', 'label_override': 'camera'},
            files={'image': ('input.jpg', _build_jpeg_with_exif(), 'image/jpeg')},
            headers={'host': 'kyanitelabs.tech', 'x-forwarded-proto': 'https'},
        )

        assert response.status_code == 200
        assert 'Sprint complete' in response.text
        assert '100% confidence' in response.text
        assert 'https://kyanitelabs.tech/declutter/listings/' in response.text
    finally:
        operator.get_operator_image_intake_service.cache_clear()
        if hasattr(operator.get_operator_analysis_adapter, 'cache_clear'):
            operator.get_operator_analysis_adapter.cache_clear()
        operator.get_operator_session_store.cache_clear()
        public_listings.get_public_listing_service.cache_clear()


def test_seller_app_home_renders_public_form() -> None:
    response = client.get('/app')

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/html')
    assert 'Turn one photo into a listing page' in response.text
    assert 'Create my listing page' in response.text


def test_seller_app_sprint_creates_public_listing_without_basic_auth(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from api.routes import operator, public_listings

    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 'local')
    monkeypatch.setenv('DECLUTTER_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('DECLUTTER_SESSION_DB_PATH', str(tmp_path / 'sessions.sqlite3'))
    monkeypatch.setenv('DECLUTTER_ANALYSIS_PROVIDER', 'mock')
    monkeypatch.setenv('DECLUTTER_PUBLIC_BASE_PATH', 'declutter')
    operator.get_operator_image_intake_service.cache_clear()
    operator.get_operator_analysis_adapter.cache_clear()
    operator.get_operator_session_store.cache_clear()
    public_listings.get_public_listing_service.cache_clear()

    try:
        response = client.post(
            '/app/sprint',
            data={'condition': 'good', 'label_override': 'camera'},
            files={'image': ('input.jpg', _build_jpeg_with_exif(), 'image/jpeg')},
            headers={'host': 'kyanitelabs.tech', 'x-forwarded-proto': 'https'},
        )

        assert response.status_code == 200
        assert 'Sprint complete' in response.text
        assert 'https://kyanitelabs.tech/declutter/listings/' in response.text
        assert 'Open beta' in response.text
    finally:
        operator.get_operator_image_intake_service.cache_clear()
        if hasattr(operator.get_operator_analysis_adapter, 'cache_clear'):
            operator.get_operator_analysis_adapter.cache_clear()
        operator.get_operator_session_store.cache_clear()
        public_listings.get_public_listing_service.cache_clear()


def test_public_listing_legacy_path_redirects_to_new_listing_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from api.routes import operator, public_listings

    monkeypatch.setenv('DECLUTTER_SHARED_ACCESS_TOKEN', 'operator-secret')
    monkeypatch.setenv('DECLUTTER_STORAGE_BACKEND', 'local')
    monkeypatch.setenv('DECLUTTER_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('DECLUTTER_SESSION_DB_PATH', str(tmp_path / 'sessions.sqlite3'))
    monkeypatch.setenv('DECLUTTER_ANALYSIS_PROVIDER', 'mock')
    operator.get_operator_image_intake_service.cache_clear()
    operator.get_operator_analysis_adapter.cache_clear()
    operator.get_operator_session_store.cache_clear()
    public_listings.get_public_listing_service.cache_clear()

    try:
        create_response = client.post(
            '/operator/sprint',
            auth=('operator', 'operator-secret'),
            data={'condition': 'good', 'label_override': 'camera'},
            files={'image': ('input.jpg', _build_jpeg_with_exif(), 'image/jpeg')},
            headers={'host': 'kyanitelabs.tech', 'x-forwarded-proto': 'https'},
        )
        listing_id = create_response.text.split('/listings/')[1].split('"')[0].split('<')[0]

        legacy_response = client.get(
            f'/public/listings/{listing_id}',
            follow_redirects=False,
        )

        assert legacy_response.status_code == 307
        assert legacy_response.headers['location'] == f'/listings/{listing_id}'
    finally:
        operator.get_operator_image_intake_service.cache_clear()
        if hasattr(operator.get_operator_analysis_adapter, 'cache_clear'):
            operator.get_operator_analysis_adapter.cache_clear()
        operator.get_operator_session_store.cache_clear()
        public_listings.get_public_listing_service.cache_clear()


def test_extract_json_object_handles_nested_json_in_fence() -> None:
    from services.analysis_adapter import _extract_json_object

    fenced = '```json\n{"items": [{"label": "camera", "confidence": 0.91}, {"label": "box", "confidence": 0.82}]}\n```'
    result = _extract_json_object(fenced)
    parsed = __import__('json').loads(result)
    assert len(parsed['items']) == 2
    assert parsed['items'][0]['label'] == 'camera'


def test_extract_json_object_handles_plain_json() -> None:
    from services.analysis_adapter import _extract_json_object

    plain = '{"items": [{"label": "book", "confidence": 0.9}]}'
    result = _extract_json_object(plain)
    parsed = __import__('json').loads(result)
    assert parsed['items'][0]['label'] == 'book'


def test_seller_app_can_be_protected_by_env_var(monkeypatch) -> None:
    monkeypatch.setenv('DECLUTTER_SELLER_AUTH_MODE', 'protected')
    from app.main import create_app

    protected_client = __import__('fastapi.testclient', fromlist=['TestClient']).TestClient(create_app())
    response = protected_client.get('/app')
    assert response.status_code == 401
