from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PublicListingResponse(BaseModel):
    listing_id: str
    public_url: str
    title: str
    description: str
    condition: str
    price_usd: float = Field(ge=0)
    category_hint: str
    created_at: datetime
