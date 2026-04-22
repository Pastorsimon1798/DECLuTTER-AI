# DECLuTTER-AI Backend Launch Notes

FastAPI backend scaffold for the same-day DECLuTTER-AI launch path.

## Local development

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
PYTHONPATH=app uvicorn app.main:app --reload
```

Health checks:

```bash
curl http://127.0.0.1:8000/health/
curl http://127.0.0.1:8000/health/readiness
python scripts/smoke_backend.py --url http://127.0.0.1:8000
```

## Container build

```bash
cd server
docker build -t declutter-ai-server:launch .
docker run --rm -p 8080:8080 --env-file .env declutter-ai-server:launch
curl http://127.0.0.1:8080/health/
python scripts/smoke_backend.py --url http://127.0.0.1:8080
```

The container installs the `prod` Python extra so strict Firebase verification and S3 storage imports are available in deployed environments.

## Environment profiles

### Public production profile

Use this for any public URL:

```bash
DECLUTTER_AUTH_MODE=strict
FIREBASE_PROJECT_ID=...
DECLUTTER_CORS_ALLOW_ORIGINS=https://your-domain.example
DECLUTTER_STORAGE_BACKEND=s3
DECLUTTER_S3_BUCKET=...
DECLUTTER_MODEL_PROVIDER=...
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
```

`/health/readiness` should return `ready_for_production: true` only after those external services are configured.

### Private demo profile

Use only behind localhost, Tailscale, VPN, or another access gate:

```bash
DECLUTTER_AUTH_MODE=scaffold
DECLUTTER_TEST_ID_TOKEN=<long-random-demo-token>
DECLUTTER_TEST_APP_CHECK_TOKEN=<long-random-demo-token>
DECLUTTER_CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
DECLUTTER_STORAGE_BACKEND=local
DECLUTTER_UPLOAD_DIR=/tmp/declutter_ai_uploads
DECLUTTER_MODEL_PROVIDER=mock-model
```

Do not expose scaffold or off auth modes on the public internet.

## Same-day launch gate

Before sharing the backend URL, verify:

1. `pytest` passes locally or in CI.
2. `/health/` returns `{"status":"ok"}`.
3. `/health/readiness` reflects the intended profile.
4. CORS contains only the launch frontend origins.
5. Protected routes reject missing auth headers.
6. No real secrets are committed; use host secrets/env vars.

## Current scaffold limitations

- Strict Firebase mode requires Firebase Admin credentials in the host environment.
- S3 storage requires cloud credentials available to boto3.
- Analysis, valuation, listing generation, and eBay publish are deterministic starter adapters until real provider integrations land.
