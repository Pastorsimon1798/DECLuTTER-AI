from __future__ import annotations

from html import escape

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.settings import Settings
from services.session_store import CashToClearSessionStore

router = APIRouter(tags=["launch"])


def get_launch_listing_service() -> CashToClearSessionStore:
    return CashToClearSessionStore()


@router.get("/", response_class=HTMLResponse)
def launch_landing_page(request: Request) -> str:
    recent_cards = []
    for listing in get_launch_listing_service().list_recent_public_listings(limit=3):
        recent_cards.append(
            f"""
            <a class="sample-card" href="{escape(listing.public_url)}">
              <span class="sample-eyebrow">Live sample</span>
              <strong>{escape(listing.title)}</strong>
              <span>${listing.price_usd:.2f} · {escape(listing.condition.title())}</span>
            </a>
            """.strip()
        )
    recent_listings_html = '\n'.join(recent_cards) or """
      <div class="sample-card muted">
        <span class="sample-eyebrow">No samples yet</span>
        <strong>The next listing you create in the app will appear here.</strong>
        <span>Use /app to generate the first public page.</span>
      </div>
    """.strip()

    canonical_url = escape(_external_path(request, '/'))
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DECLuTTER-AI — Turn clutter into live listing pages</title>
    <meta name="description" content="Upload one photo, get an AI-assisted title and starter price, and publish a shareable listing page from the same VPS-hosted flow." />
    <link rel="canonical" href="__CANONICAL_URL__" />
    <style>
      :root { color-scheme: light; --ink:#10213f; --muted:#60708f; --line:#d8e2f1; --brand:#2451ff; --brand2:#7c3aed; --bg:#f3f7ff; }
      * { box-sizing:border-box; }
      body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background: radial-gradient(circle at top left, rgba(36,81,255,.16), transparent 28rem), linear-gradient(135deg, #f7faff 0%, #edf3ff 50%, #f8f6ff 100%); }
      a { color:inherit; text-decoration:none; }
      .shell { max-width:1120px; margin:0 auto; padding:1.25rem 1rem 3rem; }
      .topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
      .brand { font-weight:950; letter-spacing:-.04em; font-size:1.05rem; }
      .nav { display:flex; gap:.7rem; flex-wrap:wrap; }
      .nav a, .ghost-link { color:#203a78; font-weight:800; }
      .hero, .panel, .sample-card { background:rgba(255,255,255,.92); border:1px solid rgba(140,154,184,.35); border-radius:24px; box-shadow:0 24px 70px rgba(20,32,51,.10); }
      .hero { display:grid; grid-template-columns:1.2fr .8fr; gap:1rem; padding:1.5rem; margin-bottom:1rem; }
      .eyebrow { margin:0 0 .55rem; color:var(--brand); font-weight:950; letter-spacing:.08em; text-transform:uppercase; font-size:.74rem; }
      h1 { margin:0; font-size:clamp(2.5rem,6vw,4.8rem); line-height:.93; letter-spacing:-.07em; }
      .lede { color:#425372; max-width:60ch; font-size:1.07rem; line-height:1.6; }
      .hero-actions { display:flex; gap:.8rem; flex-wrap:wrap; margin-top:1.1rem; }
      .btn { display:inline-flex; align-items:center; justify-content:center; border-radius:999px; padding:.95rem 1.2rem; font-weight:950; }
      .btn.primary { background:linear-gradient(135deg,var(--brand),var(--brand2)); color:white; box-shadow:0 16px 34px rgba(36,81,255,.28); }
      .btn.secondary { border:1px solid var(--line); background:white; color:#1c3971; }
      .hero-side { display:grid; gap:.8rem; }
      .stat { border:1px solid var(--line); background:white; border-radius:18px; padding:1rem; }
      .stat strong { display:block; font-size:1.4rem; letter-spacing:-.04em; }
      .layout { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }
      .panel { padding:1.25rem; }
      .step-list, .sample-grid { display:grid; gap:.8rem; }
      .step { border:1px solid var(--line); border-radius:18px; padding:.9rem; background:white; }
      .step strong { display:block; margin-bottom:.3rem; }
      .sample-grid { grid-template-columns:repeat(3,minmax(0,1fr)); }
      .sample-card { display:grid; gap:.35rem; padding:1rem; background:white; }
      .sample-card strong { font-size:1.05rem; }
      .sample-card span { color:var(--muted); }
      .sample-eyebrow { color:var(--brand); font-weight:900; letter-spacing:.06em; text-transform:uppercase; font-size:.72rem; }
      .sample-card.muted { border-style:dashed; }
      code { background:#eef2ff; border-radius:8px; padding:.14rem .4rem; }
      .microcopy { color:var(--muted); line-height:1.6; }
      @media (max-width: 900px) { .hero, .layout, .sample-grid { grid-template-columns:1fr; } }
    </style>
  </head>
  <body>
    <div class="shell">
      <header class="topbar">
        <div class="brand">DECLuTTER-AI</div>
        <nav class="nav">
          <a href="/app">Seller app</a>
          <a href="/listings">Samples</a>
          <a href="/operator">Operator</a>
        </nav>
      </header>
      <section class="hero">
        <div>
          <p class="eyebrow">Self-hosted seller workflow</p>
          <h1>Turn one photo into a live listing page.</h1>
          <p class="lede">DECLuTTER-AI is the fastest path from “I need this gone” to a shareable listing URL. Upload a photo, let the model suggest the item and starter price, then send the public page anywhere you sell.</p>
          <div class="hero-actions">
            <a class="btn primary" href="/app">Open the seller app</a>
            <a class="btn secondary" href="/operator">Private operator cockpit</a>
          </div>
          <p class="microcopy">This VPS-hosted beta already creates public pages. eBay/Firebase/cloud storage are optional later upgrades, not blockers for the current flow.</p>
        </div>
        <aside class="hero-side">
          <div class="stat"><span class="eyebrow">Current state</span><strong>Live on the VPS</strong><span class="microcopy">Public front door, seller app, operator cockpit, and standalone listing pages all ship from the same backend.</span></div>
          <div class="stat"><span class="eyebrow">Best for</span><strong>One-item quick flips</strong><span class="microcopy">Clear photos, one object per image, and manual label override when the model gets cute.</span></div>
        </aside>
      </section>
      <section class="layout">
        <article class="panel">
          <p class="eyebrow">How it works</p>
          <div class="step-list">
            <div class="step"><strong>1. Upload one item photo</strong><span class="microcopy">The app strips metadata, stores the image on the VPS, and prepares it for analysis.</span></div>
            <div class="step"><strong>2. Let the model suggest the item</strong><span class="microcopy">Home multimodal inference returns labels and confidence. Manual override is always available.</span></div>
            <div class="step"><strong>3. Share the listing page</strong><span class="microcopy">Every run produces a public page with a title, condition, starter price, and listing URL.</span></div>
          </div>
        </article>
        <article class="panel">
          <p class="eyebrow">Promotable right now</p>
          <p class="microcopy">What you can honestly show today is a working seller flow with public output. The marketing site explains it, the seller app creates it, and the listing pages are linkable.</p>
          <p class="microcopy"><strong>Health:</strong> <a class="ghost-link" href="/health/readiness"><code>/health/readiness</code></a></p>
          <p class="microcopy"><strong>Machine status:</strong> <a class="ghost-link" href="/launch/status"><code>/launch/status</code></a></p>
        </article>
      </section>
      <section class="panel" style="margin-top:1rem;">
        <p class="eyebrow">Recent listing pages</p>
        <div class="sample-grid">
          __RECENT_LISTINGS_HTML__
        </div>
      </section>
    </div>
  </body>
</html>
""".replace('__RECENT_LISTINGS_HTML__', recent_listings_html).replace(
        '__CANONICAL_URL__',
        canonical_url,
    ).strip()


@router.get("/launch/status")
def launch_status() -> dict[str, object]:
    readiness = Settings.readiness()
    return {
        "service": "DECLuTTER-AI API",
        "launch_profile": "seller_front_door_beta",
        "self_hosted_mvp_ready": readiness.self_hosted_mvp_ready,
        "production_ready": readiness.ready_for_production,
        "checks": {
            "shared_token_auth_configured": readiness.shared_token_auth_configured,
            "local_upload_storage_configured": readiness.local_upload_storage_configured,
            "sqlite_session_store_configured": readiness.sqlite_session_store_configured,
            "home_inference_configured": readiness.home_inference_configured,
            "firebase_admin_configured": readiness.firebase_admin_configured,
            "cloud_storage_configured": readiness.cloud_storage_configured,
            "multimodal_model_configured": readiness.multimodal_model_configured,
            "ebay_api_configured": readiness.ebay_api_configured,
        },
        "public_surfaces": [
            "/",
            "/app",
            "/listings/{listing_id}",
            "/health/",
            "/health/readiness",
            "/public/listings/{listing_id}",
        ],
        "limitations": [
            "The seller app and public listing pages now provide the promotable front door for the self-hosted MVP.",
            "Operator and API/docs surfaces still exist, but they are not the public marketing homepage.",
            "Home inference can use the same OpenAI-compatible/LM Studio style endpoint pattern as Achiote.",
            "Firebase, S3, and real eBay API credentials are later public-production upgrades, not blockers for the current VPS-hosted flow.",
        ],
    }


def _sanitize_host(host: str) -> str:
    if any(c in host for c in '<>"\'\n\r\t& `'):
        return 'invalid-host'
    return host


def _external_path(request: Request, internal_path: str) -> str:
    configured_prefix = os.getenv('DECLUTTER_PUBLIC_BASE_PATH', '').strip('/')
    forwarded_prefix = request.headers.get('x-forwarded-prefix', '').strip('/')
    prefix = configured_prefix or forwarded_prefix
    path = internal_path if internal_path.startswith('/') else f'/{internal_path}'
    if prefix and not path.startswith(f'/{prefix}/'):
        path = f'/{prefix}{path}'

    proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = _sanitize_host(request.headers.get('host', request.url.netloc))
    return f'{proto}://{host}{path}'
