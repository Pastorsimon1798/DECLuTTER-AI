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


class SimpleValuationRequest(BaseModel):
    category: str = Field(min_length=1)
    condition: str = "unknown"
    brand: str | None = None
    count: int = Field(default=1, ge=1)


class SimpleValuationResponse(BaseModel):
    low: float = Field(ge=0)
    mid: float = Field(ge=0)
    high: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
