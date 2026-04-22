from pydantic import BaseModel


class ListingDraftRequest(BaseModel):
    item_label: str
    condition: str


class ListingDraftResponse(BaseModel):
    title: str
    description: str
    condition: str
    price_usd: float
