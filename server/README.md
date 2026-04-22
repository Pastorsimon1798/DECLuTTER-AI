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

## Hostinger VPS deploy bundle

For the Hostinger VPS path, use the Docker Compose + Caddy bundle in:

```text
server/deploy/hostinger-vps/
```

It provides:

- `docker-compose.yml` for the backend container and HTTPS reverse proxy.
- `env.example` as the VPS-only secret template.
- `smoke.sh` for public URL health checks.

The current Hostinger MCP integration can inspect/create hosting resources, but
the visible tool surface does not expose direct VPS SSH/container deployment.
Use standard VPS SSH plus this bundle for backend launch.

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

## Cash-to-Clear session store

The backend persists session, item, decision, valuation, and listing-draft state in SQLite by default. Set `DECLUTTER_SESSION_DB_PATH` to a persistent path or mounted volume before running demos where users should keep session history across restarts.

Protected session endpoints:

- `POST /sessions` — create a Cash-to-Clear session.
- `POST /sessions/{session_id}/items` — add a detected item and persist valuation + listing draft.
- `POST /sessions/{session_id}/decisions` — record keep/donate/trash/recycle/relocate/maybe/sell decisions.
- `GET /sessions` — list the authenticated user’s session history with decision/progress totals.
- `GET /sessions/{session_id}` — retrieve durable session state and money-on-the-table totals.
- `GET /sessions/{session_id}/summary` — retrieve finish-sprint counts, estimates, and public listing links.
- `POST /sessions/{session_id}/items/{item_id}/public-listing` — generate a standalone HTML listing page for users who do not want marketplace publishing.

Public listing endpoints:

- `GET /public/listings/{listing_id}` — buyer-readable standalone HTML page.
- `GET /public/listings/{listing_id}/packet` — JSON packet for agents or exports.

## Same-day launch gate

Before sharing the backend URL, verify:

1. `pytest` passes locally or in CI.
2. `/health/` returns `{"status":"ok"}`.
3. `/health/readiness` reflects the intended profile.
4. CORS contains only the launch frontend origins.
5. Protected routes reject missing auth headers.
6. No real secrets are committed; use host secrets/env vars.

Template values from `.env.example` and `server/deploy/hostinger-vps/env.example`
are intentionally rejected by readiness checks. A container started with
placeholder values must not report production-ready.

## Current scaffold limitations

- Strict Firebase mode requires Firebase Admin credentials in the host environment.
- S3 storage requires cloud credentials available to boto3.
- Analysis, valuation, listing generation, and eBay publish are deterministic starter adapters until real provider integrations land.
