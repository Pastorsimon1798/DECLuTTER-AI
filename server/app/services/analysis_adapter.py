from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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


class OpenAICompatibleAnalysisAdapter:
    """Structured item detection through a local/OpenAI-compatible chat API.

    This follows the same deployment shape as Achiote's LM Studio/OpenAI-
    compatible provider support: a `/v1/chat/completions` base URL, model name,
    and optional bearer token. The adapter is intentionally stdlib-only so the
    self-hosted MVP does not need another Python dependency.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        upload_dir: str | None = None,
        timeout_seconds: float = 180,
        transport: Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]
        | None = None,
    ) -> None:
        if not base_url.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_BASE_URL or OPENAI_BASE_URL is required "
                "for OpenAI-compatible analysis."
            )
        if not model.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_MODEL or OPENAI_MODEL is required for "
                "OpenAI-compatible analysis."
            )

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.upload_dir = Path(
            upload_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads")
        )
        self.timeout_seconds = timeout_seconds
        self.transport = transport or self._post_json

    def run(self, image_storage_key: str) -> AnalysisResult:
        payload = self._build_payload(image_storage_key)
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"

        response = self.transport(
            f"{self.base_url}/chat/completions",
            payload,
            headers,
            self.timeout_seconds,
        )
        items = self._parse_items(response)
        return AnalysisResult(
            items=items,
            engine=f"openai-compatible:{self.model}",
            structured_output_version="2026-04-home-inference",
        )

    def _build_payload(self, image_storage_key: str) -> dict[str, Any]:
        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "Analyze this decluttering image and return ONLY JSON with "
                    "an items array. Each item must have label and confidence "
                    "between 0 and 1. Example: "
                    '{"items":[{"label":"book","confidence":0.82}]} '
                    f"Storage key: {image_storage_key}"
                ),
            }
        ]

        image_url = self._image_data_url(image_storage_key)
        if image_url:
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})

        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are DECLuTTER-AI's item detection adapter. "
                        "Return compact valid JSON only. Do not include markdown."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

    def _image_data_url(self, image_storage_key: str) -> str | None:
        candidate = (self.upload_dir / image_storage_key).resolve()
        try:
            candidate.relative_to(self.upload_dir.resolve())
        except ValueError:
            return None

        if not candidate.is_file():
            return None

        content_type = mimetypes.guess_type(candidate.name)[0] or "image/jpeg"
        encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

    @staticmethod
    def _parse_items(response: dict[str, Any]) -> list[DetectedItem]:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Inference provider returned no choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise RuntimeError("Inference provider returned an invalid choice.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Inference provider returned no message.")

        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("Inference provider returned no message content.")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Inference provider returned non-JSON item output.") from exc

        raw_items = parsed.get("items")
        if not isinstance(raw_items, list):
            raise RuntimeError("Inference provider JSON must contain an items array.")

        items: list[DetectedItem] = []
        for raw_item in raw_items[:8]:
            if not isinstance(raw_item, dict):
                continue
            label = raw_item.get("label")
            confidence = raw_item.get("confidence", 0.5)
            if not isinstance(label, str) or not label.strip():
                continue
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                confidence_value = 0.5
            items.append(
                DetectedItem(
                    label=label.strip()[:80],
                    confidence=max(0.0, min(1.0, round(confidence_value, 2))),
                )
            )

        if not items:
            raise RuntimeError("Inference provider returned no usable detected items.")

        return items

    @staticmethod
    def _post_json(
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Inference provider returned HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Inference provider request failed: {exc}") from exc


def create_analysis_adapter_from_env() -> MockStructuredAnalysisAdapter | OpenAICompatibleAnalysisAdapter:
    provider = (
        os.getenv("DECLUTTER_ANALYSIS_PROVIDER")
        or os.getenv("DECLUTTER_MODEL_PROVIDER")
        or "mock"
    ).strip().lower()

    if provider in {
        "home",
        "home_inference",
        "home-inference",
        "lmstudio",
        "lm-studio",
        "openai",
        "openai_compatible",
        "openai-compatible",
    }:
        base_url = (
            os.getenv("DECLUTTER_INFERENCE_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("LMSTUDIO_BASE_URL")
            or os.getenv("LM_STUDIO_BASE_URL")
            or ("http://127.0.0.1:1234/v1" if "lm" in provider else "")
        )
        model = (
            os.getenv("DECLUTTER_INFERENCE_MODEL")
            or os.getenv("OPENAI_MODEL")
            or os.getenv("LMSTUDIO_MODEL")
            or os.getenv("LM_STUDIO_MODEL")
            or ""
        )
        api_key = (
            os.getenv("DECLUTTER_INFERENCE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("LMSTUDIO_API_KEY")
            or os.getenv("LM_STUDIO_API_KEY")
        )
        timeout_seconds = float(os.getenv("DECLUTTER_INFERENCE_TIMEOUT_SECONDS", "180"))
        return OpenAICompatibleAnalysisAdapter(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )

    return MockStructuredAnalysisAdapter()
