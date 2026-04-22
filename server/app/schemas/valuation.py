from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    label: str
    condition: str = "unknown"


class ValuationResponse(BaseModel):
    label: str
    estimated_low_usd: float = Field(ge=0)
    estimated_high_usd: float = Field(ge=0)
    confidence: str
    comp_count: int = Field(ge=0)
    source: str
