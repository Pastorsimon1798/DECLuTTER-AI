from __future__ import annotations

from dataclasses import dataclass

from schemas.valuation import ValuationRequest, ValuationResponse


@dataclass(frozen=True)
class ComparableSalesSummary:
    source: str
    comp_count: int
    median_price: float


class MockCompsValuationService:
    """WP6 starter valuation service based on deterministic comp summaries."""

    _label_medians = {
        "electronics": 48.0,
        "book": 12.0,
        "clothing": 18.0,
        "kitchen item": 22.0,
        "toy": 16.0,
        "paper clutter": 5.0,
    }

    _condition_multipliers = {
        "new": 1.2,
        "good": 1.0,
        "fair": 0.75,
        "poor": 0.5,
        "unknown": 0.8,
    }

    def estimate(self, payload: ValuationRequest) -> ValuationResponse:
        median = self._label_medians.get(payload.label.lower(), 14.0)
        multiplier = self._condition_multipliers.get(payload.condition.lower(), 0.8)
        adjusted = median * multiplier

        summary = self._build_summary(adjusted)

        return ValuationResponse(
            label=payload.label,
            estimated_low_usd=round(adjusted * 0.75, 2),
            estimated_high_usd=round(adjusted * 1.25, 2),
            confidence=self._confidence_from_comp_count(summary.comp_count),
            comp_count=summary.comp_count,
            source=summary.source,
        )

    @staticmethod
    def _build_summary(adjusted_price: float) -> ComparableSalesSummary:
        if adjusted_price >= 30:
            return ComparableSalesSummary(source="mock-ebay-comps", comp_count=24, median_price=adjusted_price)
        if adjusted_price >= 15:
            return ComparableSalesSummary(source="mock-ebay-comps", comp_count=14, median_price=adjusted_price)
        return ComparableSalesSummary(source="mock-ebay-comps", comp_count=6, median_price=adjusted_price)

    @staticmethod
    def _confidence_from_comp_count(comp_count: int) -> str:
        if comp_count >= 20:
            return "high"
        if comp_count >= 10:
            return "medium"
        return "low"
