# Hostinger VPS deploy bundle

This folder is the concrete handoff from the launch discussion to a Hostinger
VPS deployment path.

## What happened before this bundle

- `hostinger-mcp` is installed and visible to Codex after restart.
- The exposed Hostinger MCP tools cover hosting/domain/WordPress actions.
- A read-only website lookup returned no Hostinger websites for this account.
- The MCP surface does **not** expose a direct VPS SSH/container deploy action, so
  the backend deploy path is still standard VPS SSH + Docker Compose.

## Files

- `docker-compose.yml` — runs the FastAPI backend and Caddy reverse proxy.
- `Caddyfile` — terminates HTTPS and proxies to the backend container.
- `env.example` — copy to `env.hostinger` on the VPS and fill real secrets.
- `smoke.sh` — verifies the public URL after deploy.

## DNS prerequisite

Point the launch API hostname at the VPS public IP with an `A` record.

Example:

```text
api.your-domain.example  A  <hostinger-vps-public-ip>
```

Keep DNS/name-server changes separate from app deploy work. The current
Hostinger MCP surface can change domain nameservers, but it does not expose a
safe single-record DNS editor in this session.

## VPS setup

SSH to the Hostinger VPS and install Docker + Compose if they are not present.

Ubuntu example:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Deploy self-hosted MVP

From the repo checkout on the VPS:

```bash
cd server/deploy/hostinger-vps
cp env.example env.hostinger
$EDITOR env.hostinger
docker compose --env-file env.hostinger up -d --build
docker compose --env-file env.hostinger ps
```

For the self-hosted MVP, keep:

```text
DECLUTTER_AUTH_MODE=shared_token
DECLUTTER_STORAGE_BACKEND=local
DECLUTTER_SESSION_DB_PATH=/data/declutter_ai_sessions.sqlite3
DECLUTTER_UPLOAD_DIR=/data/uploads
```

Generate a long random `DECLUTTER_SHARED_ACCESS_TOKEN` on the VPS. This replaces
Firebase for the first self-hosted version: clients send it as
`Authorization: Bearer <token>`.

You do **not** need Firebase, S3, or eBay API credentials for this self-hosted
MVP. Those are later public-production upgrades.

## Verify

```bash
./smoke.sh https://api.your-domain.example
docker compose --env-file env.hostinger logs --tail=100 declutter-api
```

Expected:

- `/health/` returns `{"status":"ok"}`.
- `/health/readiness` returns `self_hosted_mvp_ready: true` after the shared
  token, local upload directory, and SQLite path are configured.
- `/launch/status` reports the backend scaffold limitations clearly.

It is okay for `ready_for_production` to remain `false` in this mode. That flag
means the later Firebase/S3/eBay public-production stack is configured.
