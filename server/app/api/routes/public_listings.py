from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from schemas.public_listing import PublicListingResponse
from services.session_store import CashToClearSessionStore

router = APIRouter(prefix='/public/listings', tags=['public'])


@lru_cache(maxsize=1)
def get_public_listing_service() -> CashToClearSessionStore:
    return CashToClearSessionStore()


@router.get('/{listing_id}/packet', response_model=PublicListingResponse)
def get_public_listing_packet(listing_id: str) -> PublicListingResponse:
    try:
        return get_public_listing_service().get_public_listing(listing_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.get('/{listing_id}', response_class=HTMLResponse)
def get_public_listing(listing_id: str) -> str:
    try:
        return get_public_listing_service().render_public_listing_html(listing_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc
