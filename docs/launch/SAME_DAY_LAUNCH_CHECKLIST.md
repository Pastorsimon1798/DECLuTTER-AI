# Same-Day Launch Checklist

Use this checklist to get a safe public/demo backend online today without losing the path to production hardening.

## 1. Decide the launch profile

### Private demo

Use this if the goal is to show the flow today behind localhost, Tailscale, VPN, or a password/access gate.

- Auth: `DECLUTTER_AUTH_MODE=scaffold` with long random demo tokens.
- Storage: `DECLUTTER_STORAGE_BACKEND=local` and a persistent host volume.
- Model/eBay: current deterministic starter adapters.
- Do not call this production-ready.

### Public production candidate

Use this for any unauthenticated public URL.

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

## 4. Launch blockers to resolve before calling this production

- Replace deterministic mock analysis with the selected launch model/provider path.
- Configure real Firebase Admin credentials and App Check for strict mode.
- Configure durable object storage and lifecycle/deletion policy.
- Replace mock eBay publishing with the official eBay OAuth/Sell API flow.
- Add deploy-host health gates that check `/health/readiness`.

## 5. What is safe to say today

- Safe: “Backend scaffold is deployable and review-gated.”
- Safe: “Demo mode can show the Cash-to-Clear flow with deterministic starter adapters.”
- Safe: “Users can generate standalone listing HTML pages when they do not want marketplace publishing.”
- Not safe yet: “Fully production marketplace publishing is live.”
- Not safe yet: “Valuations are real marketplace-backed estimates.”
