from fastapi import APIRouter

from schemas.listing import EbayPublishRequest, EbayPublishResponse, ListingExportResponse
from services.marketplace_ebay_service import MockEbayPublisher

router = APIRouter(prefix="/marketplace/ebay", tags=["marketplace"])

publisher = MockEbayPublisher()


@router.get("/status")
def ebay_status() -> dict[str, str]:
    return {"provider": "ebay", "status": "connected_mock"}


@router.post("/publish", response_model=EbayPublishResponse)
def publish_listing(payload: EbayPublishRequest) -> EbayPublishResponse:
    return publisher.publish(payload)


@router.post("/export", response_model=ListingExportResponse)
def export_listing(payload: EbayPublishRequest) -> ListingExportResponse:
    return publisher.export_csv(payload)
