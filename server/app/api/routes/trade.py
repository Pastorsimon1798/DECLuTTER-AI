from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request, status

from schemas.trade import (
    TradeListingRequest,
    TradeListingResponse,
    TradeMatchRequest,
    TradeMatchResponse,
)
from services.trade_service import TradeService

router = APIRouter(prefix="/trade", tags=["trade"])


def _owner_uid(request: Request) -> str:
    claims = getattr(request.state, "user_claims", None)
    if isinstance(claims, dict):
        uid = claims.get("uid")
        if isinstance(uid, str) and uid:
            return uid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated user context is required.",
    )


@lru_cache(maxsize=1)
def get_trade_service() -> TradeService:
    return TradeService()


@router.post("/listings", response_model=TradeListingResponse)
def create_listing(
    payload: TradeListingRequest,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> TradeListingResponse:
    result = service.create_listing(
        user_id=_owner_uid(request),
        item_label=payload.item_label,
        description=payload.description,
        condition=payload.condition,
        valuation_median_usd=payload.valuation_median_usd,
        trade_value_credits=payload.trade_value_credits,
        latitude=payload.latitude,
        longitude=payload.longitude,
        images=payload.images,
        tags=payload.tags,
        wants_in_return=payload.wants_in_return,
    )
    return TradeListingResponse(**result)


@router.get("/listings/nearby")
def find_nearby(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    *,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> list[TradeListingResponse]:
    results = service.find_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        exclude_user_id=_owner_uid(request),
    )
    return [TradeListingResponse(**r) for r in results]


@router.post("/matches", response_model=TradeMatchResponse)
def propose_trade(
    payload: TradeMatchRequest,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    try:
        result = service.propose_trade(
            listing_id=payload.listing_id,
            requester_id=_owner_uid(request),
            offered_listing_id=payload.offered_listing_id,
            message=payload.message,
            use_credits=payload.use_credits,
            credit_amount=payload.credit_amount,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return TradeMatchResponse(**result)


@router.post("/matches/{match_id}/accept", response_model=TradeMatchResponse)
def accept_trade(
    match_id: str,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    try:
        result = service.accept_trade(match_id, user_id=_owner_uid(request))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return TradeMatchResponse(**result)


@router.post("/matches/{match_id}/decline", response_model=TradeMatchResponse)
def decline_trade(
    match_id: str,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    try:
        result = service.decline_trade(match_id, user_id=_owner_uid(request))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return TradeMatchResponse(**result)


@router.get("/credits")
def get_credit_balance(
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> dict:
    user_id = _owner_uid(request)
    balance = service._credit_store.get_credit_balance(user_id)
    history = service._credit_store.get_transaction_history(user_id, limit=20)
    return {
        "balance": balance,
        "transactions": [
            {
                "amount": t.amount,
                "item_label": t.item_label,
                "direction": t.direction,
                "created_at": t.created_at,
            }
            for t in history
        ],
    }


@router.get("/templates/{intent}")
def get_templates(intent: str) -> dict:
    from services.trade_templates import get_message_templates
    return {"intent": intent, "templates": get_message_templates(intent)}


@router.get("/conditions/{condition}")
def get_condition_details(condition: str) -> dict:
    from services.trade_templates import get_condition_checklist
    return {"condition": condition, "checklist": get_condition_checklist(condition)}


@router.get("/rules")
def get_rules() -> dict:
    from services.trade_templates import get_trade_rules
    return {"rules": get_trade_rules()}


@router.post("/matches/{match_id}/rate")
def rate_trade_partner(
    match_id: str,
    payload: dict,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> dict:
    try:
        result = service.rate_user(
            trade_match_id=match_id,
            rated_user_id=payload.get("rated_user_id", ""),
            rater_user_id=_owner_uid(request),
            rating=payload.get("rating", 0),
            tags=payload.get("tags", []),
            comment=payload.get("comment", ""),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return result


@router.get("/reputation/{user_id}")
def get_reputation(user_id: str, service: TradeService = Depends(get_trade_service)) -> dict:
    return service.get_reputation(user_id)


@router.get("/safety/{tag}")
def get_safety(tag: str) -> dict:
    from services.safety_checklists import get_safety_checklist
    return {"tag": tag, "checklist": get_safety_checklist(tag)}


@router.get("/safety")
def get_all_safety() -> dict:
    from services.safety_checklists import get_all_checklists
    return {"checklists": get_all_checklists()}


@router.post("/verify")
def verify_user(
    payload: dict,
    request: Request,
    service: TradeService = Depends(get_trade_service),
) -> dict:
    try:
        result = service.verify_user(
            user_id=_owner_uid(request),
            method=payload.get("method", ""),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return result


@router.get("/verify/{user_id}")
def get_verification(user_id: str, service: TradeService = Depends(get_trade_service)) -> dict:
    return service.get_verification_status(user_id)


@router.get("/loops")
def find_trade_loops(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    max_length: int = 4,
    *,
    service: TradeService = Depends(get_trade_service),
) -> list[dict]:
    from services.trade_matcher import find_trade_loops

    listings = service.find_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        exclude_user_id=None,
    )
    return find_trade_loops(listings, max_length=max_length)
