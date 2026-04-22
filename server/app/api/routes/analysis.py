from fastapi import APIRouter, File, UploadFile

from schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    DetectedItem,
    ImageIntakeResponse,
)
from services.image_intake import ImageIntakeService

router = APIRouter(prefix="/analysis", tags=["analysis"])

intake_service = ImageIntakeService()


@router.post("/intake", response_model=ImageIntakeResponse)
async def intake_image(image: UploadFile = File(...)) -> ImageIntakeResponse:
    result = await intake_service.intake(image)
    return ImageIntakeResponse(**result.__dict__)


@router.post("/run", response_model=AnalysisResponse)
def run_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    # Scaffold only: real AI adapter is introduced in WP5.
    items = [DetectedItem(label="unknown item", confidence=0.51)]
    return AnalysisResponse(session_id=payload.session_id, items=items)
