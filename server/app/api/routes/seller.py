from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from api.routes.operator import (
    SprintPageConfig,
    _run_sprint,
    get_operator_analysis_adapter,
    get_operator_image_intake_service,
    get_operator_session_store,
    render_sprint_page,
)
from services.image_intake import ImageIntakeService
from services.session_store import CashToClearSessionStore

router = APIRouter(prefix="/app", tags=["seller"])
SELLER_APP_OWNER_UID = "public-seller-studio"

SELLER_PAGE_CONFIG = SprintPageConfig(
    page_title="DECLuTTER AI — Web Seller App",
    hero_eyebrow="Web companion",
    hero_title="Turn one photo into a listing page",
    hero_lede=(
        "Upload a single item photo, let DECLuTTER-AI name it, estimate a "
        "starter price, and hand you a public listing URL you can share anywhere. "
        "This is the web companion to the mobile decluttering app."
    ),
    access_badge="Open beta",
    access_badge_class="ok",
    run_eyebrow="Create a listing",
    action_path="/app/sprint",
    submit_label="Create my listing page",
)


@router.get("", response_class=HTMLResponse)
def seller_app_home(request: Request) -> str:
    return render_sprint_page(
        request,
        result=None,
        error=None,
        config=SELLER_PAGE_CONFIG,
    )


@router.post("/sprint", response_class=HTMLResponse)
async def run_seller_sprint(
    request: Request,
    image: UploadFile = File(...),
    condition: str = Form(default="unknown"),
    label_override: str = Form(default=""),
    intake_service: ImageIntakeService = Depends(get_operator_image_intake_service),
    store: CashToClearSessionStore = Depends(get_operator_session_store),
) -> str:
    try:
        result = await _run_sprint(
            request=request,
            image=image,
            condition=condition,
            label_override=label_override,
            owner_uid=SELLER_APP_OWNER_UID,
            intake_service=intake_service,
            analysis_adapter=get_operator_analysis_adapter(),
            store=store,
        )
        return render_sprint_page(
            request,
            result=result,
            error=None,
            config=SELLER_PAGE_CONFIG,
        )
    except (RuntimeError, ValueError) as exc:
        return render_sprint_page(
            request,
            result=None,
            error=str(exc),
            config=SELLER_PAGE_CONFIG,
        )
