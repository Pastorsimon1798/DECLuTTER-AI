from fastapi import APIRouter

from schemas.valuation import ValuationRequest, ValuationResponse

router = APIRouter(prefix="/valuation", tags=["valuation"])


@router.post("/estimate", response_model=ValuationResponse)
def estimate_value(payload: ValuationRequest) -> ValuationResponse:
    # Scaffold only: real comps logic lands in WP6.
    return ValuationResponse(
        label=payload.label,
        estimated_low_usd=10.0,
        estimated_high_usd=20.0,
        confidence="low",
    )
