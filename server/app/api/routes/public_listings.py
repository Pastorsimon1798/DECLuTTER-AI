from fastapi import APIRouter

router = APIRouter(prefix="/public/listings", tags=["public"])


@router.get("/{listing_id}")
def get_public_listing(listing_id: str) -> dict[str, str]:
    return {
        "listing_id": listing_id,
        "status": "stub",
        "note": "Public packet endpoint scaffolded.",
    }
