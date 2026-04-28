from functools import lru_cache

from fastapi import APIRouter, Depends

from schemas.valuation import (
    PriceFeedbackRequest,
    PriceFeedbackResponse,
    RecordedSaleRequest,
    RecordedSaleResponse,
    SimpleValuationRequest,
    SimpleValuationResponse,
    ValuationOverrideRequest,
    ValuationRequest,
    ValuationResponse,
)
from services.valuation_service import ResearchBackedValuationService

router = APIRouter(prefix="/valuation", tags=["valuation"])

# Lookup tables for the simple valuation endpoint (WP5)
_CATEGORY_RANGES: dict[str, tuple[float, float]] = {
    "electronics": (10.0, 500.0),
    "books": (1.0, 15.0),
    "clothing": (2.0, 40.0),
    "furniture": (20.0, 300.0),
}

_CONDITION_MULTIPLIERS: dict[str, float] = {
    "new": 1.0,
    "good": 0.7,
    "fair": 0.4,
    "poor": 0.15,
}


@lru_cache(maxsize=1)
def get_valuation_service() -> ResearchBackedValuationService:
    return ResearchBackedValuationService()


@router.post("/estimate", response_model=ValuationResponse)
def estimate_value(
    payload: ValuationRequest,
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> ValuationResponse:
    return service.estimate(payload)


@router.post("/override", response_model=ValuationResponse)
def override_value(
    payload: ValuationOverrideRequest,
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> ValuationResponse:
    return service.estimate(
        ValuationRequest(label=payload.label, condition=payload.condition),
        user_override_usd=payload.override_usd,
    )


@router.post("/feedback", response_model=PriceFeedbackResponse)
def price_feedback(
    payload: PriceFeedbackRequest,
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> PriceFeedbackResponse:
    result = service.record_feedback(
        label=payload.label,
        expected_median_usd=payload.expected_median_usd,
        reason=payload.reason,
        source=payload.source,
    )
    return PriceFeedbackResponse(
        label=result["label"],
        previous_median_usd=result["previous_median_usd"],
        feedback_median_usd=result["feedback_median_usd"],
        status=result["status"],
        message="Feedback recorded. If enough users agree, the price will auto-adjust.",
    )


@router.post("/record-sale", response_model=RecordedSaleResponse)
def record_sale(
    payload: RecordedSaleRequest,
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> RecordedSaleResponse:
    result = service.record_sale(
        label=payload.label,
        sale_price_usd=payload.sale_price_usd,
        condition=payload.condition,
        platform=payload.platform,
        notes=payload.notes,
    )
    return RecordedSaleResponse(
        label=result["label"],
        sale_price_usd=result["sale_price_usd"],
        recorded_at=result["recorded_at"],
        message="Sale recorded. If enough sales are reported, the price will auto-adjust.",
    )


@router.get("/health")
def valuation_health(
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> dict:
    return service.get_health()


@router.get("/history/{label}")
def price_history(
    label: str,
    limit: int = 20,
    service: ResearchBackedValuationService = Depends(get_valuation_service),
) -> dict:
    return {
        "label": label,
        "history": service.get_price_history(label, limit),
    }


@router.post("", response_model=SimpleValuationResponse)
def simple_estimate_value(payload: SimpleValuationRequest) -> SimpleValuationResponse:
    low_base, high_base = _CATEGORY_RANGES.get(payload.category.lower(), (1.0, 20.0))
    multiplier = _CONDITION_MULTIPLIERS.get(payload.condition.lower(), 0.5)
    low = round(low_base * multiplier * payload.count, 2)
    high = round(high_base * multiplier * payload.count, 2)
    mid = round((low + high) / 2, 2)
    return SimpleValuationResponse(low=low, mid=mid, high=high, confidence=0.3)
