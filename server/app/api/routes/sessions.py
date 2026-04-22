from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request, status

from schemas.session import (
    CashToClearSessionResponse,
    SessionCreateRequest,
    SessionDecisionRequest,
    SessionDecisionResponse,
    SessionItemCreateRequest,
    SessionItemResponse,
)
from services.session_store import CashToClearSessionStore

router = APIRouter(prefix='/sessions', tags=['sessions'])


@lru_cache(maxsize=1)
def get_cash_to_clear_service() -> CashToClearSessionStore:
    return CashToClearSessionStore()


@router.post('', response_model=CashToClearSessionResponse)
def create_session(
    request: Request,
    payload: SessionCreateRequest | None = None,
) -> CashToClearSessionResponse:
    return get_cash_to_clear_service().create_session(
        _owner_uid(request),
        payload or SessionCreateRequest(),
    )


@router.get('/{session_id}', response_model=CashToClearSessionResponse)
def get_session(request: Request, session_id: str) -> CashToClearSessionResponse:
    try:
        return get_cash_to_clear_service().get_session(_owner_uid(request), session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.post('/{session_id}/items', response_model=SessionItemResponse)
def add_item(
    request: Request,
    session_id: str,
    payload: SessionItemCreateRequest,
) -> SessionItemResponse:
    try:
        return get_cash_to_clear_service().add_item(_owner_uid(request), session_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.post('/{session_id}/decisions', response_model=SessionDecisionResponse)
def record_decision(
    request: Request,
    session_id: str,
    payload: SessionDecisionRequest,
) -> SessionDecisionResponse:
    try:
        return get_cash_to_clear_service().record_decision(
            _owner_uid(request),
            session_id,
            payload,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def _owner_uid(request: Request) -> str:
    claims = getattr(request.state, 'user_claims', None)
    if isinstance(claims, dict):
        uid = claims.get('uid')
        if isinstance(uid, str) and uid:
            return uid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Authenticated user context is required.',
    )
