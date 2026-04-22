from fastapi import APIRouter, File, UploadFile

from schemas.analysis import AnalysisRequest, AnalysisResponse, ImageIntakeResponse
from services.analysis_adapter import MockStructuredAnalysisAdapter
from services.image_intake import ImageIntakeService

router = APIRouter(prefix="/analysis", tags=["analysis"])

intake_service = ImageIntakeService()
analysis_adapter = MockStructuredAnalysisAdapter()


@router.post("/intake", response_model=ImageIntakeResponse)
async def intake_image(image: UploadFile = File(...)) -> ImageIntakeResponse:
    result = await intake_service.intake(image)
    return ImageIntakeResponse(**result.__dict__)


@router.post("/run", response_model=AnalysisResponse)
def run_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    result = analysis_adapter.run(payload.image_storage_key)
    return AnalysisResponse(
        session_id=payload.session_id,
        items=result.items,
        engine=result.engine,
        structured_output_version=result.structured_output_version,
    )
