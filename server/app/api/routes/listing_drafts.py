from fastapi import APIRouter

from schemas.listing import ListingDraftRequest, ListingDraftResponse

router = APIRouter(prefix="/listing-drafts", tags=["listing"])


@router.post("/generate", response_model=ListingDraftResponse)
def generate_listing(payload: ListingDraftRequest) -> ListingDraftResponse:
    # Scaffold only: real generator lands in WP8.
    return ListingDraftResponse(
        title=f"{payload.item_label} - {payload.condition}",
        description="Auto-generated draft. Review before publishing.",
        condition=payload.condition,
        price_usd=19.99,
    )
