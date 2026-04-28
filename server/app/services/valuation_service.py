from __future__ import annotations

from dataclasses import dataclass

from schemas.valuation import ValuationRequest, ValuationResponse
from services.llm_price_estimator import LlmPriceEstimator
from services.price_database import PriceDatabase


@dataclass(frozen=True)
class ComparableSalesSummary:
    source: str
    comp_count: int
    median_price: float


class ResearchBackedValuationService:
    """Valuation service backed by a local price database with LLM fallback.

    Lookup order:
    1. Query local SQLite price database (seeded data + cached LLM estimates)
    2. On miss: prompt local LM Studio for a price estimate
    3. Store LLM estimate in database for future cache hits
    4. User can always manually override any price
    """

    def __init__(
        self,
        price_database: PriceDatabase | None = None,
        llm_estimator: LlmPriceEstimator | None = None,
    ) -> None:
        self._db = price_database or PriceDatabase()
        self._estimator = llm_estimator or LlmPriceEstimator()

    def estimate(
        self,
        payload: ValuationRequest,
        user_override_usd: float | None = None,
    ) -> ValuationResponse:
        if user_override_usd is not None and user_override_usd >= 0:
            price_range = self._db.record_manual_override(
                payload.label, user_override_usd
            )
        else:
            price_range = self._db.get_price_range(payload.label)

            if price_range is None:
                # Cache miss — try LLM fallback
                llm_result = self._estimator.estimate(payload.label)
                if llm_result is not None:
                    low, median, high = llm_result
                    price_range = self._db.record_llm_estimate(
                        payload.label, low, median, high
                    )
                else:
                    # Absolute fallback: generic unknown-item range
                    price_range = self._db.record_llm_estimate(
                        payload.label, 5.0, 15.0, 30.0
                    )

        age_days, stale_warning = self._db.get_staleness(price_range)

        return ValuationResponse(
            label=payload.label,
            estimated_low_usd=round(price_range.low_price, 2),
            estimated_high_usd=round(price_range.high_price, 2),
            median_usd=round(price_range.median_price, 2),
            confidence=price_range.confidence,
            comp_count=price_range.comp_count,
            source=price_range.source,
            disclaimer=self._disclaimer_for_source(price_range.source),
            user_override=user_override_usd,
            age_days=age_days,
            stale_warning=stale_warning,
        )

    def record_feedback(
        self,
        label: str,
        expected_median_usd: float,
        reason: str = "",
        source: str = "user",
    ) -> dict:
        """Record user feedback about a price being incorrect."""
        return self._db.record_feedback(label, expected_median_usd, reason, source)

    def record_sale(
        self,
        label: str,
        sale_price_usd: float,
        condition: str = "unknown",
        platform: str = "",
        notes: str = "",
    ) -> dict:
        """Record an actual sale price for community aggregation."""
        return self._db.record_sale(
            label, sale_price_usd, condition, platform, notes
        )

    def get_health(self) -> dict:
        """Return data-quality health report."""
        return self._db.get_health()

    def get_price_history(self, label: str, limit: int = 20) -> list[dict]:
        """Return price change history for a label."""
        return self._db.get_price_history(label, limit)

    @staticmethod
    def _disclaimer_for_source(source: str) -> str:
        disclaimers = {
            "seeded": (
                "Based on general resale guide data for common household items — "
                "not live market comps."
            ),
            "llm_estimate": (
                "Estimated by local AI based on general knowledge — "
                "no market data available for this specific item."
            ),
            "manual": "Price set by user.",
            "external": "Based on external marketplace data.",
            "community": (
                "Based on anonymized community-contributed sale prices — "
                "actual market data."
            ),
        }
        return disclaimers.get(source, "Source unknown.")
