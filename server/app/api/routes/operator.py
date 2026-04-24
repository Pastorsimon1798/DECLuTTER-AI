from __future__ import annotations

import html
import os
import secrets
from dataclasses import dataclass
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from schemas.session import SessionCreateRequest, SessionItemCreateRequest
from services.analysis_adapter import (
    MockStructuredAnalysisAdapter,
    OpenAICompatibleAnalysisAdapter,
    create_analysis_adapter_from_env,
)
from services.image_intake import ImageIntakeService
from services.session_store import CashToClearSessionStore
from services.storage_adapter import create_storage_adapter_from_env

router = APIRouter(prefix='/operator', tags=['operator'])
security = HTTPBasic(auto_error=False)
OPERATOR_OWNER_UID = 'self-hosted-operator'


@dataclass(frozen=True)
class OperatorSprintResult:
    storage_key: str
    detected_label: str
    confidence: float
    session_id: str
    item_id: str
    listing_id: str
    public_listing_url: str
    engine: str
    estimated_low_usd: float
    estimated_high_usd: float
    price_usd: float


@dataclass(frozen=True)
class SprintPageConfig:
    page_title: str
    hero_eyebrow: str
    hero_title: str
    hero_lede: str
    access_badge: str
    access_badge_class: str
    run_eyebrow: str
    action_path: str
    submit_label: str


OPERATOR_PAGE_CONFIG = SprintPageConfig(
    page_title='DECLuTTER-AI Operator',
    hero_eyebrow='Private MVP cockpit',
    hero_title='Cash-to-Clear Operator',
    hero_lede=(
        'Upload one photo, let the backend detect the item, create a session, '
        'draft a listing, and produce a public listing URL. Secrets stay '
        'server-side behind Basic auth.'
    ),
    access_badge='Locked',
    access_badge_class='lock',
    run_eyebrow='Run a sprint',
    action_path='/operator/sprint',
    submit_label='Run Cash-to-Clear sprint',
)


@lru_cache(maxsize=1)
def get_operator_image_intake_service() -> ImageIntakeService:
    return ImageIntakeService(storage=create_storage_adapter_from_env())


@lru_cache(maxsize=1)
def get_operator_analysis_adapter() -> (
    MockStructuredAnalysisAdapter | OpenAICompatibleAnalysisAdapter
):
    return create_analysis_adapter_from_env()


@lru_cache(maxsize=1)
def get_operator_session_store() -> CashToClearSessionStore:
    return CashToClearSessionStore()


def _require_operator_auth(
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> HTTPBasicCredentials:
    expected_password = os.getenv('DECLUTTER_OPERATOR_PASSWORD') or os.getenv(
        'DECLUTTER_SHARED_ACCESS_TOKEN',
    )
    expected_username = os.getenv('DECLUTTER_OPERATOR_USERNAME', 'operator').strip()
    if not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Operator access requires DECLUTTER_OPERATOR_PASSWORD or DECLUTTER_SHARED_ACCESS_TOKEN.',
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Operator credentials are required.',
            headers={'WWW-Authenticate': 'Basic realm="DECLuTTER-AI Operator"'},
        )

    if not secrets.compare_digest(credentials.username, expected_username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Operator credentials are required.',
            headers={'WWW-Authenticate': 'Basic realm="DECLuTTER-AI Operator"'},
        )

    if not secrets.compare_digest(credentials.password, expected_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Operator credentials are required.',
            headers={'WWW-Authenticate': 'Basic realm="DECLuTTER-AI Operator"'},
        )

    return credentials


@router.get('', response_class=HTMLResponse)
def operator_home(
    request: Request,
    _credentials: HTTPBasicCredentials = Depends(_require_operator_auth),
) -> str:
    return render_sprint_page(
        request,
        result=None,
        error=None,
        config=OPERATOR_PAGE_CONFIG,
    )


@router.post('/sprint', response_class=HTMLResponse)
async def run_operator_sprint(
    request: Request,
    image: UploadFile = File(...),
    condition: str = Form(default='unknown'),
    label_override: str = Form(default=''),
    _credentials: HTTPBasicCredentials = Depends(_require_operator_auth),
    intake_service: ImageIntakeService = Depends(get_operator_image_intake_service),
    store: CashToClearSessionStore = Depends(get_operator_session_store),
) -> str:
    try:
        result = await _run_sprint(
            request=request,
            image=image,
            condition=condition,
            label_override=label_override,
            owner_uid=OPERATOR_OWNER_UID,
            intake_service=intake_service,
            analysis_adapter=get_operator_analysis_adapter(),
            store=store,
        )
        return render_sprint_page(request, result=result, error=None, config=OPERATOR_PAGE_CONFIG)
    except (RuntimeError, ValueError) as exc:
        return render_sprint_page(
            request,
            result=None,
            error=str(exc),
            config=OPERATOR_PAGE_CONFIG,
        )


async def _run_sprint(
    request: Request,
    image: UploadFile,
    condition: str,
    label_override: str,
    owner_uid: str,
    intake_service: ImageIntakeService,
    analysis_adapter: MockStructuredAnalysisAdapter | OpenAICompatibleAnalysisAdapter,
    store: CashToClearSessionStore,
) -> OperatorSprintResult:
    intake = await intake_service.intake(image)
    manual_label = label_override.strip()
    try:
        analysis = analysis_adapter.run(intake.storage_key)
        detected = analysis.items[0] if analysis.items else None
        engine = analysis.engine
    except RuntimeError:
        if not manual_label:
            raise
        detected = None
        engine = 'manual-override'

    if detected is None and not manual_label:
        raise RuntimeError('No detected items were returned. Add a manual label and retry.')

    label = manual_label or detected.label
    confidence = detected.confidence if detected is not None else 1.0
    session = store.create_session(
        owner_uid,
        SessionCreateRequest(image_storage_key=intake.storage_key),
    )
    item = store.add_item(
        owner_uid,
        session.session_id,
        SessionItemCreateRequest(label=label, condition=condition.strip() or 'unknown'),
    )
    listing = store.create_public_listing(
        owner_uid,
        session.session_id,
        item.item_id,
    )

    return OperatorSprintResult(
        storage_key=intake.storage_key,
        detected_label=label,
        confidence=confidence,
        session_id=session.session_id,
        item_id=item.item_id,
        listing_id=listing.listing_id,
        public_listing_url=_external_path(request, listing.public_url),
        engine=engine,
        estimated_low_usd=item.valuation.estimated_low_usd,
        estimated_high_usd=item.valuation.estimated_high_usd,
        price_usd=listing.price_usd,
    )


def _sanitize_host(host: str) -> str:
    if any(c in host for c in '<>"\'\n\r\t'):
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


def render_sprint_page(
    request: Request,
    result: OperatorSprintResult | None,
    error: str | None,
    *,
    config: SprintPageConfig,
) -> str:
    result_html = ''
    if error:
        result_html = f'''
        <section class="panel error-panel" aria-live="polite">
          <p class="eyebrow">Sprint interrupted</p>
          <h2>Could not finish this run</h2>
          <p>{html.escape(error)}</p>
          <p class="hint">Try a clearer image, add a manual label, or switch inference back to mock mode if the model server is overloaded.</p>
        </section>
        '''
    elif result:
        listing_url = html.escape(result.public_listing_url)
        engine_label = 'Home vision inference' if result.engine.startswith('openai-compatible:') else 'Deterministic mock analysis'
        result_html = f'''
        <section class="panel result-panel" aria-live="polite">
          <div class="result-head">
            <div>
              <p class="eyebrow">Sprint complete</p>
              <h2>{html.escape(result.detected_label).title()} is ready to list</h2>
            </div>
            <span class="price-pill">${result.price_usd:.2f}</span>
          </div>
          <div class="result-grid">
            <article>
              <span class="metric-label">Detected item</span>
              <strong>{html.escape(result.detected_label)}</strong>
              <small>{result.confidence:.0%} confidence · {html.escape(engine_label)}</small>
            </article>
            <article>
              <span class="metric-label">Estimated range</span>
              <strong>${result.estimated_low_usd:.2f} - ${result.estimated_high_usd:.2f}</strong>
              <small>Starter valuation for pricing review</small>
            </article>
            <article>
              <span class="metric-label">Session</span>
              <code>{html.escape(result.session_id)}</code>
              <small>Stored on the VPS SQLite volume</small>
            </article>
            <article>
              <span class="metric-label">Item</span>
              <code>{html.escape(result.item_id)}</code>
              <small>Listing packet generated</small>
            </article>
          </div>
          <div class="listing-box">
            <span class="metric-label">Public listing URL</span>
            <a href="{listing_url}">{listing_url}</a>
            <button class="secondary" type="button" data-copy="{listing_url}">Copy URL</button>
          </div>
        </section>
        '''

    action = html.escape(_external_path(request, config.action_path))
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(config.page_title)}</title>
    <meta name="description" content="{html.escape(config.hero_lede)}" />
    <link rel="canonical" href="{html.escape(_external_path(request, request.url.path))}" />
    <style>
      :root {{ color-scheme: light; --ink:#142033; --muted:#64748b; --line:#d8e0ee; --brand:#3157ff; --brand2:#7c3aed; --bg:#eef4ff; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: radial-gradient(circle at top left, rgba(49,87,255,.18), transparent 32rem), linear-gradient(135deg, #f7fbff 0%, #edf3ff 45%, #f8f6ff 100%); }}
      .shell {{ max-width: 1120px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
      .hero {{ display: grid; grid-template-columns: 1.2fr .8fr; gap: 1rem; align-items: stretch; margin-bottom: 1rem; }}
      .hero-card, .panel, .step-card {{ background: rgba(255,255,255,.92); border: 1px solid rgba(140,154,184,.35); border-radius: 24px; box-shadow: 0 24px 70px rgba(20,32,51,.10); }}
      .hero-card {{ padding: 1.5rem; overflow: hidden; position: relative; }}
      .hero-card:after {{ content:""; position:absolute; right:-4rem; top:-4rem; width:12rem; height:12rem; background: radial-gradient(circle, rgba(124,58,237,.18), transparent 70%); }}
      .eyebrow {{ margin: 0 0 .55rem; color: var(--brand); font-weight: 900; letter-spacing: .08em; text-transform: uppercase; font-size: .74rem; }}
      h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4rem); line-height: .95; letter-spacing: -.06em; }}
      h2 {{ margin: .1rem 0 .5rem; letter-spacing: -.03em; }}
      .lede {{ max-width: 64ch; color: #40506a; font-size: 1.05rem; line-height: 1.55; }}
      .status-card {{ padding: 1rem; display: grid; gap: .75rem; }}
      .status-row {{ display:flex; gap:.6rem; align-items:center; justify-content:space-between; border:1px solid var(--line); border-radius:16px; padding:.75rem; background:#fff; }}
      .badge {{ display:inline-flex; align-items:center; border-radius:999px; padding:.35rem .65rem; font-weight:900; font-size:.78rem; }}
      .badge.ok {{ color:#05603a; background:#ddfbe8; }} .badge.lock {{ color:#5b21b6; background:#ede9fe; }} .badge.warn {{ color:#92400e; background:#fef3c7; }}
      .layout {{ display:grid; grid-template-columns: .9fr 1.1fr; gap:1rem; align-items:start; }}
      .panel {{ padding: 1.25rem; }}
      .steps {{ display:grid; gap:.7rem; }}
      .step-card {{ padding:.9rem; display:grid; grid-template-columns:auto 1fr; gap:.75rem; box-shadow:none; }}
      .step-num {{ width:2rem; height:2rem; border-radius:999px; display:grid; place-items:center; color:white; background:linear-gradient(135deg,var(--brand),var(--brand2)); font-weight:900; }}
      form {{ display:grid; gap:1rem; }}
      label {{ display:block; font-weight:900; }}
      .field-hint, .hint, small {{ color: var(--muted); font-size:.9rem; line-height:1.45; }}
      input[type="text"], select, input[type="file"] {{ width:100%; margin-top:.4rem; border:1px solid #bdc8da; border-radius:14px; padding:.82rem; background:#fff; font:inherit; }}
      input[type="file"] {{ border-style:dashed; }}
      button {{ border:0; border-radius:999px; background:linear-gradient(135deg,var(--brand),var(--brand2)); color:white; padding:.9rem 1.2rem; font-weight:950; cursor:pointer; box-shadow:0 14px 30px rgba(49,87,255,.25); }}
      button.secondary {{ background:#10213f; box-shadow:none; padding:.65rem .95rem; }}
      .result-panel {{ margin-top:1rem; border-color:#9bd7b4; background:linear-gradient(180deg,#f1fff6,#fff); }}
      .error-panel {{ margin-top:1rem; border-color:#fecaca; background:linear-gradient(180deg,#fff5f5,#fff); }}
      .result-head {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
      .price-pill {{ border-radius:999px; background:#062e1b; color:#d9ffe8; padding:.65rem .9rem; font-size:1.2rem; font-weight:950; }}
      .result-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.75rem; margin-top:1rem; }}
      .result-grid article, .listing-box {{ border:1px solid var(--line); border-radius:18px; padding:.85rem; background:white; display:grid; gap:.25rem; }}
      .metric-label {{ color:var(--muted); font-size:.72rem; font-weight:950; letter-spacing:.08em; text-transform:uppercase; }}
      code {{ background:#eef2ff; color:#1e3a8a; border-radius:8px; padding:.18rem .35rem; overflow-wrap:anywhere; }}
      a {{ color:#234bd7; font-weight:900; overflow-wrap:anywhere; }}
      .listing-box {{ margin-top:.85rem; }}
      .preview-card {{ min-height: 13rem; border-radius:18px; border:1px dashed #aab8d0; background: linear-gradient(135deg,#f8fbff,#eef4ff); display:grid; place-items:center; text-align:center; color:var(--muted); padding:1rem; }}
      @media (max-width: 850px) {{ .hero, .layout, .result-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:2.4rem; }} }}
    </style>
  </head>
  <body>
    <div class="shell">
      <section class="hero">
        <div class="hero-card">
          <p class="eyebrow">{html.escape(config.hero_eyebrow)}</p>
          <h1>{html.escape(config.hero_title)}</h1>
          <p class="lede">{html.escape(config.hero_lede)}</p>
        </div>
        <aside class="status-card">
          <div class="status-row"><span>Access</span><span class="badge {html.escape(config.access_badge_class)}">{html.escape(config.access_badge)}</span></div>
          <div class="status-row"><span>Storage</span><span class="badge ok">VPS local</span></div>
          <div class="status-row"><span>Inference</span><span class="badge ok">Home model</span></div>
          <div class="status-row"><span>Output</span><span class="badge warn">Review before selling</span></div>
        </aside>
      </section>
      <section class="layout">
        <aside class="panel steps">
          <p class="eyebrow">What happens</p>
          <div class="step-card"><span class="step-num">1</span><div><strong>Upload photo</strong><br><span class="field-hint">JPG, PNG, or WebP. Metadata is stripped before storage.</span></div></div>
          <div class="step-card"><span class="step-num">2</span><div><strong>Detect item</strong><br><span class="field-hint">Uses the configured model path; manual label can override uncertainty.</span></div></div>
          <div class="step-card"><span class="step-num">3</span><div><strong>Create listing</strong><br><span class="field-hint">Session, item, valuation, draft, and public listing are created together.</span></div></div>
          <div class="preview-card">Tip: use a clear, close-up photo of one item for the cleanest listing draft.</div>
        </aside>
        <main class="panel">
          <p class="eyebrow">{html.escape(config.run_eyebrow)}</p>
          <form action="{action}" method="post" enctype="multipart/form-data">
            <label>Photo
              <input name="image" type="file" accept="image/jpeg,image/png,image/webp" required />
              <span class="field-hint">One item per sprint works best right now.</span>
            </label>
            <label>Condition
              <select name="condition">
                <option value="unknown">Unknown</option>
                <option value="new">New</option>
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="poor">Poor</option>
              </select>
            </label>
            <label>Manual label override <span class="hint">optional</span>
              <input name="label_override" type="text" placeholder="e.g. camera, shoes, toy" />
              <span class="field-hint">Use this if the model sees the right object but names it poorly.</span>
            </label>
            <button type="submit">{html.escape(config.submit_label)}</button>
          </form>
          {result_html}
        </main>
      </section>
    </div>
    <script>
      document.querySelectorAll('[data-copy]').forEach((button) => {{
        button.addEventListener('click', async () => {{
          await navigator.clipboard.writeText(button.dataset.copy);
          button.textContent = 'Copied';
          setTimeout(() => button.textContent = 'Copy URL', 1400);
        }});
      }});
    </script>
  </body>
</html>'''
