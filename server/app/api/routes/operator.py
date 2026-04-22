from __future__ import annotations

import html
import os
import secrets
from dataclasses import dataclass
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from schemas.analysis import AnalysisRequest
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
    if not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Operator access requires DECLUTTER_OPERATOR_PASSWORD or DECLUTTER_SHARED_ACCESS_TOKEN.',
        )

    if credentials is None or not secrets.compare_digest(
        credentials.password,
        expected_password,
    ):
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
    return _render_page(request, result=None, error=None)


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
            intake_service=intake_service,
            analysis_adapter=get_operator_analysis_adapter(),
            store=store,
        )
        return _render_page(request, result=result, error=None)
    except (RuntimeError, ValueError) as exc:
        return _render_page(request, result=None, error=str(exc))


async def _run_sprint(
    request: Request,
    image: UploadFile,
    condition: str,
    label_override: str,
    intake_service: ImageIntakeService,
    analysis_adapter: MockStructuredAnalysisAdapter | OpenAICompatibleAnalysisAdapter,
    store: CashToClearSessionStore,
) -> OperatorSprintResult:
    intake = await intake_service.intake(image)
    analysis = analysis_adapter.run(intake.storage_key)
    detected = analysis.items[0] if analysis.items else None
    if detected is None and not label_override.strip():
        raise RuntimeError('No detected items were returned. Add a manual label and retry.')

    label = label_override.strip() or detected.label
    confidence = detected.confidence if detected is not None else 1.0
    session = store.create_session(
        OPERATOR_OWNER_UID,
        SessionCreateRequest(image_storage_key=intake.storage_key),
    )
    item = store.add_item(
        OPERATOR_OWNER_UID,
        session.session_id,
        SessionItemCreateRequest(label=label, condition=condition.strip() or 'unknown'),
    )
    listing = store.create_public_listing(
        OPERATOR_OWNER_UID,
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
        engine=analysis.engine,
        estimated_low_usd=item.valuation.estimated_low_usd,
        estimated_high_usd=item.valuation.estimated_high_usd,
        price_usd=listing.price_usd,
    )


def _external_path(request: Request, internal_path: str) -> str:
    configured_prefix = os.getenv('DECLUTTER_PUBLIC_BASE_PATH', '').strip('/')
    forwarded_prefix = request.headers.get('x-forwarded-prefix', '').strip('/')
    prefix = configured_prefix or forwarded_prefix
    path = internal_path if internal_path.startswith('/') else f'/{internal_path}'
    if prefix and not path.startswith(f'/{prefix}/'):
        path = f'/{prefix}{path}'

    proto = request.headers.get('x-forwarded-proto', request.url.scheme)
    host = request.headers.get('host', request.url.netloc)
    return f'{proto}://{host}{path}'


def _render_page(
    request: Request,
    result: OperatorSprintResult | None,
    error: str | None,
) -> str:
    result_html = ''
    if error:
        result_html = f'<section class="error"><h2>Could not finish sprint</h2><p>{html.escape(error)}</p></section>'
    elif result:
        listing_url = html.escape(result.public_listing_url)
        result_html = f'''
        <section class="result">
          <h2>Sprint complete</h2>
          <dl>
            <dt>Detected item</dt><dd>{html.escape(result.detected_label)} ({result.confidence:.2f})</dd>
            <dt>Engine</dt><dd>{html.escape(result.engine)}</dd>
            <dt>Session</dt><dd><code>{html.escape(result.session_id)}</code></dd>
            <dt>Item</dt><dd><code>{html.escape(result.item_id)}</code></dd>
            <dt>Estimate</dt><dd>${result.estimated_low_usd:.2f} - ${result.estimated_high_usd:.2f}</dd>
            <dt>Listing price</dt><dd>${result.price_usd:.2f}</dd>
            <dt>Public listing</dt><dd><a href="{listing_url}">{listing_url}</a></dd>
          </dl>
          <p><button type="button" onclick="navigator.clipboard.writeText('{listing_url}')">Copy listing URL</button></p>
        </section>
        '''

    action = html.escape(_external_path(request, '/operator/sprint'))
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DECLuTTER-AI Operator</title>
    <style>
      body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 840px; padding: 0 1rem; color: #182033; background: #f6f8fb; }}
      main {{ background: white; border: 1px solid #d8deea; border-radius: 18px; padding: 1.5rem; box-shadow: 0 14px 38px rgba(24,32,51,.08); }}
      h1 {{ margin-top: 0; }}
      label {{ display: block; font-weight: 700; margin-top: 1rem; }}
      input, select, button {{ font: inherit; }}
      input[type="text"], select {{ width: 100%; box-sizing: border-box; padding: .7rem; border: 1px solid #b9c3d6; border-radius: 10px; margin-top: .35rem; }}
      input[type="file"] {{ margin-top: .5rem; }}
      button {{ margin-top: 1rem; border: 0; border-radius: 999px; background: #234bd7; color: white; padding: .8rem 1.1rem; font-weight: 800; cursor: pointer; }}
      .hint {{ color: #596579; }}
      .result, .error {{ margin-top: 1.25rem; border-radius: 14px; padding: 1rem; }}
      .result {{ background: #eefbf3; border: 1px solid #9dd7b1; }}
      .error {{ background: #fff2f2; border: 1px solid #f0b3b3; }}
      dt {{ font-weight: 800; margin-top: .75rem; }}
      dd {{ margin-left: 0; }}
      code {{ background: rgba(35,75,215,.08); padding: .1rem .3rem; border-radius: 6px; }}
    </style>
  </head>
  <body>
    <main>
      <h1>DECLuTTER-AI Operator</h1>
      <p class="hint">Private MVP flow: upload one item photo, run analysis, create a Cash-to-Clear session, create the first item, and generate a public listing page. The backend token stays server-side behind HTTP Basic auth.</p>
      <form action="{action}" method="post" enctype="multipart/form-data">
        <label>Photo
          <input name="image" type="file" accept="image/jpeg,image/png,image/webp" required />
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
        </label>
        <button type="submit">Run Cash-to-Clear sprint</button>
      </form>
      {result_html}
    </main>
  </body>
</html>'''
