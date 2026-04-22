from fastapi import APIRouter

from schemas.listing import ListingDraftRequest, ListingDraftResponse
from services.listing_service import ListingDraftService

router = APIRouter(prefix="/listing-drafts", tags=["listing"])

draft_service = ListingDraftService()


@router.post("/generate", response_model=ListingDraftResponse)
def generate_listing(payload: ListingDraftRequest) -> ListingDraftResponse:
    return draft_service.generate(payload)
