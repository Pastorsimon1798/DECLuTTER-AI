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
    label: str = Field(min_length=1)
    condition: str = 'unknown'


class SessionDecisionRequest(BaseModel):
    item_id: str = Field(min_length=1)
    decision: DecisionValue
    note: str | None = None


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
