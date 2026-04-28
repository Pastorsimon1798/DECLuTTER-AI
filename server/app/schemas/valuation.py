from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
    label: str
    condition: str = "unknown"


class ValuationResponse(BaseModel):
    label: str
    estimated_low_usd: float = Field(ge=0)
    estimated_high_usd: float = Field(ge=0)
    median_usd: float = Field(default=0.0, ge=0)
    confidence: str
    comp_count: int = Field(ge=0)
    source: str = Field(default="unknown")
    disclaimer: str = Field(default="")
    user_override: float | None = Field(default=None, ge=0)
    age_days: int = Field(default=0, ge=0)
    stale_warning: str = Field(default="")


class ValuationOverrideRequest(BaseModel):
    label: str
    condition: str = "unknown"
    override_usd: float = Field(ge=0)


class PriceFeedbackRequest(BaseModel):
    label: str
    expected_median_usd: float = Field(ge=0, description="What the user thinks the price should be")
    reason: str = Field(default="", max_length=500)
    source: str = Field(default="user", pattern="^(user|sale|market)$")


class PriceFeedbackResponse(BaseModel):
    label: str
    previous_median_usd: float
    feedback_median_usd: float
    status: str
    message: str


class RecordedSaleRequest(BaseModel):
    label: str
    sale_price_usd: float = Field(ge=0)
    condition: str = "unknown"
    platform: str = Field(default="", max_length=100)
    notes: str = Field(default="", max_length=500)


class RecordedSaleResponse(BaseModel):
    label: str
    sale_price_usd: float
    recorded_at: str
    message: str


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
