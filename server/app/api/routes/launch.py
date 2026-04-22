from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from core.settings import Settings

router = APIRouter(tags=["launch"])


@router.get("/", response_class=HTMLResponse)
def launch_landing_page() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DECLuTTER-AI Launch API</title>
    <style>
      body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 3rem auto; max-width: 760px; padding: 0 1rem; line-height: 1.5; color: #172033; }
      .card { border: 1px solid #d7ddea; border-radius: 16px; padding: 1.25rem; background: #f8fbff; }
      a { color: #2357d7; font-weight: 700; }
      code { background: #eef2ff; border-radius: 6px; padding: 0.1rem 0.35rem; }
    </style>
  </head>
  <body>
    <main class="card">
      <h1>DECLuTTER-AI Launch API</h1>
      <p>Same-day backend scaffold for Cash-to-Clear: protected image intake, starter analysis, valuation, listing drafts, mock eBay publish/export, public listing packets, and launch health checks.</p>
      <p><strong>Launch gate:</strong> use <a href="/health/readiness">/health/readiness</a> before calling this production-ready.</p>
      <p><strong>API docs:</strong> inspect <a href="/docs">/docs</a> or machine-readable <a href="/openapi.json">/openapi.json</a>.</p>
      <p><strong>Status JSON:</strong> <a href="/launch/status">/launch/status</a>.</p>
    </main>
  </body>
</html>
""".strip()


@router.get("/launch/status")
def launch_status() -> dict[str, object]:
    readiness = Settings.readiness()
    return {
        "service": "DECLuTTER-AI API",
        "launch_profile": "backend_scaffold",
        "production_ready": readiness.ready_for_production,
        "checks": {
            "firebase_admin_configured": readiness.firebase_admin_configured,
            "cloud_storage_configured": readiness.cloud_storage_configured,
            "multimodal_model_configured": readiness.multimodal_model_configured,
            "ebay_api_configured": readiness.ebay_api_configured,
        },
        "public_surfaces": [
            "/",
            "/health/",
            "/health/readiness",
            "/docs",
            "/openapi.json",
            "/public/listings/{listing_id}",
        ],
        "limitations": [
            "Private routes require Firebase Auth/App Check headers unless explicitly running a private scaffold demo.",
            "Analysis, valuation, listing generation, and eBay publish currently use deterministic starter adapters.",
            "Production launch still requires live Firebase Admin credentials, durable object storage, model provider configuration, and real eBay API credentials.",
        ],
    }
