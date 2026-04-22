from fastapi import APIRouter, File, UploadFile

from schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ImageIntakeResponse,
    IntakeSessionResponse,
)
from services.analysis_adapter import MockStructuredAnalysisAdapter
from services.image_intake import ImageIntakeService
from services.storage_adapter import LocalSignedUploadAdapter

router = APIRouter(prefix="/analysis", tags=["analysis"])

intake_service = ImageIntakeService()
analysis_adapter = MockStructuredAnalysisAdapter()
upload_adapter = LocalSignedUploadAdapter()


@router.post("/intake/session", response_model=IntakeSessionResponse)
def create_intake_session() -> IntakeSessionResponse:
    session = upload_adapter.create_upload_session()
    return IntakeSessionResponse(**session.__dict__)


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
