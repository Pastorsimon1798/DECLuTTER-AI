from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

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
def create_session(payload: SessionCreateRequest) -> CashToClearSessionResponse:
    return get_cash_to_clear_service().create_session(payload)


@router.get('/{session_id}', response_model=CashToClearSessionResponse)
def get_session(session_id: str) -> CashToClearSessionResponse:
    try:
        return get_cash_to_clear_service().get_session(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.post('/{session_id}/items', response_model=SessionItemResponse)
def add_item(session_id: str, payload: SessionItemCreateRequest) -> SessionItemResponse:
    try:
        return get_cash_to_clear_service().add_item(session_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc


@router.post('/{session_id}/decisions', response_model=SessionDecisionResponse)
def record_decision(
    session_id: str,
    payload: SessionDecisionRequest,
) -> SessionDecisionResponse:
    try:
        return get_cash_to_clear_service().record_decision(session_id, payload)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc).strip("'"),
        ) from exc
