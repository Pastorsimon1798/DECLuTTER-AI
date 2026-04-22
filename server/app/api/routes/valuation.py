from fastapi import APIRouter

from schemas.valuation import ValuationRequest, ValuationResponse
from services.valuation_service import MockCompsValuationService

router = APIRouter(prefix="/valuation", tags=["valuation"])

valuation_service = MockCompsValuationService()


@router.post("/estimate", response_model=ValuationResponse)
def estimate_value(payload: ValuationRequest) -> ValuationResponse:
    return valuation_service.estimate(payload)
