from pydantic import BaseModel, Field


class ListingDraftRequest(BaseModel):
    item_label: str
    condition: str
    estimated_low_usd: float = Field(ge=0)
    estimated_high_usd: float = Field(ge=0)


class ListingChecklistItem(BaseModel):
    id: str
    label: str
    done: bool = False


class ListingDraftResponse(BaseModel):
    title: str
    description: str
    condition: str
    price_usd: float = Field(ge=0)
    category_hint: str
    review_checklist: list[ListingChecklistItem]


class EbayPublishRequest(BaseModel):
    title: str
    description: str
    condition: str
    price_usd: float = Field(ge=0)


class EbayPublishResponse(BaseModel):
    provider: str
    listing_id: str
    status: str
    listing_url: str


class ListingExportResponse(BaseModel):
    format: str
    content: str
