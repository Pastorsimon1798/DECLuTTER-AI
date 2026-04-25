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
    recent_listings_html = "\n".join(recent_cards) or """
      <div class="sample-card muted">
        <span class="sample-eyebrow">No samples yet</span>
        <strong>The next listing you create will appear here.</strong>
        <span>Use the web seller app to generate the first public page.</span>
      </div>
    """.strip()

    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DECLuTTER-AI — The ADHD-friendly decluttering assistant</title>
    <meta name="description" content="Take a photo of your clutter, get AI-assisted item detection, and power through a 10-minute decision sprint. Keep, donate, trash, relocate, or maybe — one zone at a time." />
    <link rel="canonical" href="__CANONICAL_URL__" />
    <style>
      :root { color-scheme: light; --ink:#10213f; --muted:#60708f; --line:#d8e2f1; --brand:#2451ff; --brand2:#7c3aed; --bg:#f3f7ff; --adhd:#ff6b35; }
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
      .eyebrow.adhd { color:var(--adhd); }
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
      .tag { display:inline-block; background:#fff0e8; color:#c44d1a; border-radius:999px; padding:.25rem .7rem; font-size:.78rem; font-weight:800; }
      @media (max-width: 900px) { .hero, .layout, .sample-grid { grid-template-columns:1fr; } }
    </style>
  </head>
  <body>
    <div class="shell">
      <header class="topbar">
        <div class="brand">DECLuTTER-AI</div>
        <nav class="nav">
          <a href="/app">Web seller app</a>
          <a href="/listings">Samples</a>
          <a href="/operator">Operator</a>
        </nav>
      </header>
      <section class="hero">
        <div>
          <p class="eyebrow adhd">ADHD-friendly decluttering</p>
          <h1>One photo. One sprint. One less pile.</h1>
          <p class="lede">DECLuTTER-AI is a mobile decluttering assistant built for brains that need structure, novelty, and a ticking clock. Snap a photo of any clutter zone, see what's in it, then blast through a 10-minute decision sprint: <strong>Keep, Donate, Trash, Relocate, or Maybe</strong>. No overwhelm. No marathon sessions. Just one zone at a time.</p>
          <div class="hero-actions">
            <span class="tag">Flutter app — coming to TestFlight</span>
            <a class="btn secondary" href="/app">Try the web seller app</a>
          </div>
          <p class="microcopy">The mobile app is the main experience. The web seller app below is a companion for quick listing-page generation from any device.</p>
        </div>
        <aside class="hero-side">
          <div class="stat"><span class="eyebrow">How it works</span><strong>10-minute sprints</strong><span class="microcopy">ADHD timeboxing built in. The timer keeps you moving so you don't get stuck on one item.</span></div>
          <div class="stat"><span class="eyebrow">Decision framework</span><strong>Five clear actions</strong><span class="microcopy">Keep, Donate, Trash, Relocate, Maybe. No ambiguity. Decisions are logged so you can review later.</span></div>
          <div class="stat"><span class="eyebrow">Detection</span><strong>On-device AI</strong><span class="microcopy">The camera sees what's in the pile and groups similar items. No manual tagging required.</span></div>
        </aside>
      </section>
      <section class="layout">
        <article class="panel">
          <p class="eyebrow">The mobile flow</p>
          <div class="step-list">
            <div class="step"><strong>1. Snap a zone photo</strong><span class="microcopy">Point the camera at one pile — a drawer, a shelf, a corner. The app detects what's there.</span></div>
            <div class="step"><strong>2. Start the 10-minute sprint</strong><span class="microcopy">The focus timer starts. You have ten minutes to make a decision on every detected group.</span></div>
            <div class="step"><strong>3. Decide every group</strong><span class="microcopy">Tap Keep, Donate, Trash, Relocate, or Maybe for each cluster. Add a quick note if you need context later.</span></div>
            <div class="step"><strong>4. Get a summary</strong><span class="microcopy">When the timer ends, see your decisions, estimated value, and next actions. Export to CSV.</span></div>
          </div>
        </article>
        <article class="panel">
          <p class="eyebrow">What works today</p>
          <p class="microcopy"><strong>Backend (live):</strong> The FastAPI backend is deployed and running on a VPS. It handles image intake, item analysis, session storage, and public listing page generation.</p>
          <p class="microcopy"><strong>Web seller app (live):</strong> Upload a single photo via the web form, get an AI-suggested label and starter price, and generate a shareable public listing page.</p>
          <p class="microcopy"><strong>Flutter app (in development):</strong> Camera capture, mock detection overlays, focus timer, and decision logging are implemented. On-device inference and valuation are in progress.</p>
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
""".replace("__RECENT_LISTINGS_HTML__", recent_listings_html).replace(
        "__CANONICAL_URL__",
        _external_path(request, "/"),
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
            "The web seller app and public listing pages provide a promotable front door for the self-hosted MVP.",
            "The Flutter mobile app is the primary product experience and is still in active development.",
            "Home inference can use the same OpenAI-compatible/LM Studio style endpoint pattern as Achiote.",
            "Firebase, S3, and real eBay API credentials are later public-production upgrades, not blockers for the current VPS-hosted flow.",
        ],
    }


def _sanitize_host(host: str) -> str:
    if any(c in host for c in '<>"\'\n\r\t'):
        return "invalid-host"
    return host


def _external_path(request: Request, internal_path: str) -> str:
    configured_prefix = os.getenv("DECLUTTER_PUBLIC_BASE_PATH", "").strip("/")
    forwarded_prefix = request.headers.get("x-forwarded-prefix", "").strip("/")
    prefix = configured_prefix or forwarded_prefix
    path = internal_path if internal_path.startswith("/") else f"/{internal_path}"
    if prefix and not path.startswith(f"/{prefix}/"):
        path = f"/{prefix}{path}"

    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = _sanitize_host(request.headers.get("host", request.url.netloc))
    return f"{proto}://{host}{path}"
