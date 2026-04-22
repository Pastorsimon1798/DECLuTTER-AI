from fastapi import APIRouter

from schemas.analysis import AnalysisRequest, AnalysisResponse, DetectedItem

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisResponse)
def run_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    # Scaffold only: real AI adapter is introduced in WP5.
    items = [DetectedItem(label="unknown item", confidence=0.51)]
    return AnalysisResponse(session_id=payload.session_id, items=items)
