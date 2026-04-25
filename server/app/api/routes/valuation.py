from functools import lru_cache

from fastapi import APIRouter, Depends

from schemas.valuation import (
    SimpleValuationRequest,
    SimpleValuationResponse,
    ValuationRequest,
    ValuationResponse,
)
from services.valuation_service import MockCompsValuationService

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
def get_valuation_service() -> MockCompsValuationService:
    return MockCompsValuationService()


@router.post("/estimate", response_model=ValuationResponse)
def estimate_value(
    payload: ValuationRequest,
    service: MockCompsValuationService = Depends(get_valuation_service),
) -> ValuationResponse:
    return service.estimate(payload)


@router.post("", response_model=SimpleValuationResponse)
def simple_estimate_value(payload: SimpleValuationRequest) -> SimpleValuationResponse:
    low_base, high_base = _CATEGORY_RANGES.get(payload.category.lower(), (1.0, 20.0))
    multiplier = _CONDITION_MULTIPLIERS.get(payload.condition.lower(), 0.5)
    low = round(low_base * multiplier * payload.count, 2)
    high = round(high_base * multiplier * payload.count, 2)
    mid = round((low + high) / 2, 2)
    return SimpleValuationResponse(low=low, mid=mid, high=high, confidence=0.3)
