from functools import lru_cache

from fastapi import APIRouter, Depends

from schemas.valuation import ValuationRequest, ValuationResponse
from services.valuation_service import MockCompsValuationService

router = APIRouter(prefix="/valuation", tags=["valuation"])


@lru_cache(maxsize=1)
def get_valuation_service() -> MockCompsValuationService:
    return MockCompsValuationService()


@router.post("/estimate", response_model=ValuationResponse)
def estimate_value(
    payload: ValuationRequest,
    service: MockCompsValuationService = Depends(get_valuation_service),
) -> ValuationResponse:
    return service.estimate(payload)
