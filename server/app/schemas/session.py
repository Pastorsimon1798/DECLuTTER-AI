from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from schemas.listing import ListingDraftResponse
from schemas.valuation import ValuationResponse

DecisionValue = Literal['keep', 'donate', 'trash', 'recycle', 'relocate', 'maybe', 'sell']


class SessionCreateRequest(BaseModel):
    image_storage_key: str | None = None


class SessionItemCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    condition: str = 'unknown'


class SessionDecisionRequest(BaseModel):
    item_id: str = Field(min_length=1)
    decision: DecisionValue
    note: str | None = Field(default=None, max_length=500)


class SessionDecisionResponse(BaseModel):
    item_id: str
    decision: DecisionValue
    note: str | None
    decided_at: datetime


class SessionItemResponse(BaseModel):
    item_id: str
    label: str
    condition: str
    valuation: ValuationResponse
    listing_draft: ListingDraftResponse
    decision: SessionDecisionResponse | None = None
    created_at: datetime


class CashToClearSessionResponse(BaseModel):
    session_id: str
    image_storage_key: str | None
    created_at: datetime
    items: list[SessionItemResponse] = Field(default_factory=list)
    money_on_table_low_usd: float = Field(ge=0)
    money_on_table_high_usd: float = Field(ge=0)


class SessionPublicListingSummary(BaseModel):
    item_id: str
    listing_id: str
    public_url: str
    title: str


class CashToClearSessionSummaryResponse(BaseModel):
    session_id: str
    image_storage_key: str | None
    created_at: datetime
    total_items: int = Field(ge=0)
    decided_items: int = Field(ge=0)
    decision_counts: dict[str, int]
    total_estimated_low_usd: float = Field(ge=0)
    total_estimated_high_usd: float = Field(ge=0)
    money_on_table_low_usd: float = Field(ge=0)
    money_on_table_high_usd: float = Field(ge=0)
    public_listings: list[SessionPublicListingSummary] = Field(default_factory=list)


class CashToClearSessionHistoryItem(BaseModel):
    session_id: str
    image_storage_key: str | None
    created_at: datetime
    total_items: int = Field(ge=0)
    decided_items: int = Field(ge=0)
    money_on_table_low_usd: float = Field(ge=0)
    money_on_table_high_usd: float = Field(ge=0)
    public_listing_count: int = Field(ge=0)


class CashToClearSessionHistoryResponse(BaseModel):
    sessions: list[CashToClearSessionHistoryItem] = Field(default_factory=list)
