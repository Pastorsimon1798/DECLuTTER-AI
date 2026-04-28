from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from services.price_database import PriceDatabase


class LlmPriceEstimator:
    """Falls back to the local LM Studio instance for price estimates on cache miss.

    This is entirely offline — no external APIs. The model is prompted with a
    simple text-only request to return a JSON price range for a given item label.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        self.base_url = (base_url or os.getenv("DECLUTTER_INFERENCE_BASE_URL", "")).rstrip("/")
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[:-3]
        self.model = model or os.getenv("DECLUTTER_INFERENCE_MODEL", "")
        self.timeout_seconds = timeout_seconds

    def estimate(self, label: str) -> tuple[float, float, float] | None:
        """Return (low, median, high) or None if the model fails."""
        if not self.base_url or not self.model:
            return None

        prompt = (
            f'What is the typical garage-sale or Facebook Marketplace resale price '
            f'range (in USD) for a used "{label}"? '
            f'Reply with ONLY a JSON object in this exact format: '
            f'{{"low": 5, "median": 15, "high": 30}}. '
            f'Do not include markdown, explanations, or any other text.'
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a pricing assistant. You know typical used-item "
                        "prices for garage sales and online resale. "
                        "Reply with ONLY valid JSON. No markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 128,
        }

        try:
            response = self._post_json(
                f"{self.base_url}/api/v0/chat/completions",
                payload,
            )
        except RuntimeError:
            return None

        content = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            return None

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        low = parsed.get("low")
        median = parsed.get("median")
        high = parsed.get("high")

        if not all(isinstance(v, (int, float)) for v in (low, median, high)):
            return None

        low_f = max(0.0, float(low))
        median_f = max(low_f, float(median))
        high_f = max(median_f, float(high))

        return (low_f, median_f, high_f)

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LM price estimator returned HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"LM price estimator request failed: {exc}") from exc
