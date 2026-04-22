from __future__ import annotations

from schemas.listing import ListingChecklistItem, ListingDraftRequest, ListingDraftResponse


class ListingDraftService:
    """WP8 starter listing generator with review checklist output."""

    _category_map = {
        "electronics": "Consumer Electronics",
        "book": "Books & Magazines",
        "clothing": "Clothing, Shoes & Accessories",
        "toy": "Toys & Hobbies",
        "kitchen item": "Home & Garden",
        "paper clutter": "Collectibles",
    }

    def generate(self, payload: ListingDraftRequest) -> ListingDraftResponse:
        category = self._category_map.get(payload.item_label.lower(), "Everything Else")
        midpoint = (payload.estimated_low_usd + payload.estimated_high_usd) / 2
        suggested_price = round(midpoint, 2)

        title = f"{payload.item_label.title()} - {payload.condition.title()}"
        description = (
            f"Auto-generated draft for {payload.item_label}. "
            "Please verify model/brand details, defects, and shipping dimensions before publish."
        )

        checklist = [
            ListingChecklistItem(id="photos", label="Add 3+ clear photos"),
            ListingChecklistItem(id="defects", label="Confirm defects and wear notes"),
            ListingChecklistItem(id="shipping", label="Verify package size and shipping option"),
        ]

        return ListingDraftResponse(
            title=title,
            description=description,
            condition=payload.condition,
            price_usd=suggested_price,
            category_hint=category,
            review_checklist=checklist,
        )
