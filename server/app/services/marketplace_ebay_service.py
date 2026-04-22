from __future__ import annotations

from uuid import uuid4

from schemas.listing import EbayPublishRequest, EbayPublishResponse, ListingExportResponse


class MockEbayPublisher:
    """WP9 starter publisher/exporter for eBay integration flow."""

    def publish(self, payload: EbayPublishRequest) -> EbayPublishResponse:
        listing_id = f"EBAY-{uuid4().hex[:10].upper()}"
        return EbayPublishResponse(
            provider="ebay",
            listing_id=listing_id,
            status="submitted_for_review",
            listing_url=f"https://www.ebay.com/itm/{listing_id}",
        )

    def export_csv(self, payload: EbayPublishRequest) -> ListingExportResponse:
        escaped_title = payload.title.replace('"', '""')
        escaped_description = payload.description.replace('"', '""')
        line = f'"{escaped_title}","{escaped_description}","{payload.condition}",{payload.price_usd}'
        return ListingExportResponse(format="csv", content=line)
