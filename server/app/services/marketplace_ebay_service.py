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

    @staticmethod
    def _sanitize_csv_cell(value: str) -> str:
        """Escape quotes and neutralize formula injection vectors."""
        escaped = value.replace('"', '""')
        # Prefix formula-triggering characters to prevent Excel formula execution
        if escaped and escaped[0] in ('=', '+', '-', '@'):
            escaped = "'" + escaped
        # Replace newlines/tabs with spaces to preserve row structure
        escaped = escaped.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return escaped

    def export_csv(self, payload: EbayPublishRequest) -> ListingExportResponse:
        title = self._sanitize_csv_cell(payload.title)
        description = self._sanitize_csv_cell(payload.description)
        condition = self._sanitize_csv_cell(payload.condition)
        line = f'"{title}","{description}","{condition}",{payload.price_usd}'
        return ListingExportResponse(format="csv", content=line)
