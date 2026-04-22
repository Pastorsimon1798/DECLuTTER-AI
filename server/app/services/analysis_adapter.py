from __future__ import annotations

import hashlib
from dataclasses import dataclass

from schemas.analysis import DetectedItem


@dataclass(frozen=True)
class AnalysisResult:
    items: list[DetectedItem]
    engine: str
    structured_output_version: str


class MockStructuredAnalysisAdapter:
    """WP5 starter adapter that emits deterministic structured detections.

    This is intentionally lightweight and deterministic so test runs are stable
    before real multimodal model integration lands.
    """

    _label_pool = [
        "clothing",
        "electronics",
        "paper clutter",
        "toy",
        "book",
        "kitchen item",
    ]

    def run(self, image_storage_key: str) -> AnalysisResult:
        digest = hashlib.sha256(image_storage_key.encode("utf-8")).digest()

        primary_index = digest[0] % len(self._label_pool)
        secondary_index = digest[1] % len(self._label_pool)

        primary = DetectedItem(
            label=self._label_pool[primary_index],
            confidence=round(0.6 + (digest[2] / 255.0) * 0.35, 2),
        )

        secondary = DetectedItem(
            label=self._label_pool[secondary_index],
            confidence=round(0.35 + (digest[3] / 255.0) * 0.3, 2),
        )

        unique_items = [primary]
        if secondary.label != primary.label:
            unique_items.append(secondary)

        return AnalysisResult(
            items=unique_items,
            engine="mock-structured-v1",
            structured_output_version="2026-04-wp5-starter",
        )
