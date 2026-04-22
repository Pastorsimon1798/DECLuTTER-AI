# Same-Day Launch Checklist

Use this checklist to get a safe public/demo backend online today without losing the path to production hardening.

## 1. Decide the launch profile

### Self-hosted MVP

Use this first if the goal is to get the Cash-to-Clear loop working on your VPS
without Firebase, S3, or automatic eBay posting.

- Auth: `DECLUTTER_AUTH_MODE=shared_token` with one long random bearer token.
- Storage: `DECLUTTER_STORAGE_BACKEND=local` and a persistent VPS volume.
- Database: SQLite at a persistent `DECLUTTER_SESSION_DB_PATH`.
- Model/eBay: current deterministic starter adapters.
- Listings: generate drafts and standalone public HTML listing pages; publish to
  marketplaces manually for now.
- Health gate: `/health/readiness` should report `self_hosted_mvp_ready: true`.

### Public production candidate

Use this later for real public users and automated marketplace integrations.

- Auth: `DECLUTTER_AUTH_MODE=strict`.
- Firebase Admin credentials are configured in the host environment.
- App Check token verification is enabled.
- Storage: `DECLUTTER_STORAGE_BACKEND=s3` and `DECLUTTER_S3_BUCKET` set.
- Cloud credentials are supplied through host identity/secrets, not the repo.
- CORS is restricted to the launch frontend domain.
- `/health/readiness` returns `ready_for_production: true`.

## 2. Backend smoke commands

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
python -m compileall -q app tests
PYTHONPATH=app uvicorn app.main:app --host 127.0.0.1 --port 8080
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:8080/health/
curl -fsS http://127.0.0.1:8080/health/readiness
python scripts/smoke_backend.py --url http://127.0.0.1:8080
```

## 3. Container smoke commands

```bash
cd server
cp .env.example .env
# Edit .env in your secret manager or local shell; do not commit it.
docker build -t declutter-ai-server:launch .
docker run --rm --env-file .env -p 8080:8080 declutter-ai-server:launch
curl -fsS http://127.0.0.1:8080/health/
python scripts/smoke_backend.py --url http://127.0.0.1:8080
```

## 4. Hostinger VPS deploy path

Use this when the backend should run on a Hostinger VPS as the self-hosted MVP:

```bash
cd server/deploy/hostinger-vps
cp env.example env.hostinger
# Fill env.hostinger on the VPS only; do not commit it.
docker compose --env-file env.hostinger up -d --build
./smoke.sh https://api.your-domain.example
```

Prerequisites:

- DNS `A` record for the API hostname points to the VPS public IP.
- Ports `80` and `443` are reachable so Caddy can issue HTTPS certificates.
- `env.hostinger` uses `DECLUTTER_AUTH_MODE=shared_token` with a long random
  bearer token.
- `DECLUTTER_STORAGE_BACKEND=local`, `DECLUTTER_UPLOAD_DIR`, and
  `DECLUTTER_SESSION_DB_PATH` point at persistent VPS/container volume paths.

## 5. Launch blockers to resolve before calling this production

- Replace deterministic mock analysis with the selected launch model/provider path.
- Configure real Firebase Admin credentials and App Check for strict mode.
- Configure durable object storage and lifecycle/deletion policy.
- Replace mock eBay publishing with the official eBay OAuth/Sell API flow.
- Add deploy-host health gates that check `/health/readiness`.

## 6. What is safe to say today

- Safe: “Backend scaffold is deployable and review-gated.”
- Safe: “Self-hosted MVP mode can show the Cash-to-Clear flow with deterministic starter adapters.”
- Safe: “Users can generate standalone listing HTML pages when they do not want marketplace publishing.”
- Not safe yet: “Fully production marketplace publishing is live.”
- Not safe yet: “Valuations are real marketplace-backed estimates.”
