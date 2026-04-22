from functools import lru_cache

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ImageIntakeResponse,
    IntakeSessionResponse,
)
from services.analysis_adapter import (
    MockStructuredAnalysisAdapter,
    OpenAICompatibleAnalysisAdapter,
    create_analysis_adapter_from_env,
)
from services.image_intake import ImageIntakeService
from services.storage_adapter import (
    LocalSignedUploadAdapter,
    create_storage_adapter_from_env,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def build_image_intake_service() -> ImageIntakeService:
    return ImageIntakeService(storage=create_storage_adapter_from_env())


@lru_cache(maxsize=1)
def get_image_intake_service() -> ImageIntakeService:
    return build_image_intake_service()


@lru_cache(maxsize=1)
def get_analysis_adapter() -> (
    MockStructuredAnalysisAdapter | OpenAICompatibleAnalysisAdapter
):
    return create_analysis_adapter_from_env()


upload_adapter = LocalSignedUploadAdapter()


@router.post("/intake/session", response_model=IntakeSessionResponse)
def create_intake_session() -> IntakeSessionResponse:
    session = upload_adapter.create_upload_session()
    return IntakeSessionResponse(**session.__dict__)


@router.post("/intake", response_model=ImageIntakeResponse)
async def intake_image(
    image: UploadFile = File(...),
    service: ImageIntakeService = Depends(get_image_intake_service),
) -> ImageIntakeResponse:
    result = await service.intake(image)
    return ImageIntakeResponse(**result.__dict__)


@router.post("/run", response_model=AnalysisResponse)
def run_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    try:
        analysis_adapter = get_analysis_adapter()
        result = analysis_adapter.run(payload.image_storage_key)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return AnalysisResponse(
        session_id=payload.session_id,
        items=result.items,
        engine=result.engine,
        structured_output_version=result.structured_output_version,
    )
