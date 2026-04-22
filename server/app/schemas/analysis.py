from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    session_id: str
    image_storage_key: str


class ImageIntakeResponse(BaseModel):
    storage_key: str
    content_type: str
    original_size_bytes: int = Field(ge=1)
    sanitized_size_bytes: int = Field(ge=1)


class IntakeSessionResponse(BaseModel):
    storage_key: str
    upload_url: str
    required_headers: dict[str, str]
    expires_in_seconds: int = Field(ge=1)


class DetectedItem(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)


class AnalysisResponse(BaseModel):
    session_id: str
    items: list[DetectedItem]
    engine: str
    structured_output_version: str
