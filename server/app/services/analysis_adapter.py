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
from typing import Any, Callable, Protocol

from schemas.analysis import DetectedItem


@dataclass(frozen=True)
class AnalysisResult:
    items: list[DetectedItem]
    engine: str
    structured_output_version: str


class ImageResolver:
    """Resolves storage keys to base64 data URLs with path-traversal protection.

    This is intentionally separate from the adapters so every vision provider
    reuses the same safety checks.
    """

    _MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB cap before base64 encoding

    def __init__(self, upload_dir: str | None = None) -> None:
        self.upload_dir = Path(
            upload_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads")
        )

    @staticmethod
    def sanitize_storage_key(key: str) -> str:
        """Validate storage key to prevent prompt injection and path traversal."""
        sanitized = key.strip()
        if not sanitized:
            raise RuntimeError("Empty image storage key.")
        if not all(c.isalnum() or c in "._-/" for c in sanitized):
            raise RuntimeError("Invalid characters in image storage key.")
        if ".." in sanitized:
            raise RuntimeError("Path traversal detected in image storage key.")
        return sanitized

    def resolve(self, image_storage_key: str) -> str | None:
        """Return a base64 data URL for the image, or None if not found / unsafe.

        NOTE: This does NOT re-run character-level sanitization. Callers that
        need validation (e.g., adapters building prompts) should call
        :meth:`sanitize_storage_key` before passing the key here.
        """
        candidate = (self.upload_dir / image_storage_key).resolve()
        # Resolve symlinks and verify the real path is still under upload_dir
        try:
            real_path = candidate.resolve()
            real_upload_dir = self.upload_dir.resolve()
            real_path.relative_to(real_upload_dir)
        except (ValueError, OSError):
            return None

        if not real_path.is_file():
            return None

        file_size = real_path.stat().st_size
        if file_size > self._MAX_IMAGE_BYTES:
            raise RuntimeError(
                f"Image size ({file_size} bytes) exceeds the "
                f"{self._MAX_IMAGE_BYTES // (1024 * 1024)}MB analysis limit."
            )

        content_type = mimetypes.guess_type(real_path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(real_path.read_bytes()).decode("ascii")
        return f"data:{content_type};base64,{encoded}"


class AnalysisAdapter(Protocol):
    """Duck-typed interface for all vision analysis adapters."""

    def run(self, image_storage_key: str) -> AnalysisResult:
        ...


# ---------------------------------------------------------------------------
# Mock adapter
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# OpenAI-compatible adapter (covers OpenAI, Groq, Together, LM Studio,
# Ollama's /v1 endpoint, Azure OpenAI, Fireworks, Cerebras, etc.)
# ---------------------------------------------------------------------------


class OpenAICompatibleAnalysisAdapter:
    """Structured item detection through any OpenAI-compatible chat API.

    This follows the same deployment shape as Achiote's LM Studio/OpenAI-
    compatible provider support: a ``/v1/chat/completions`` base URL, model
    name, and optional bearer token. The adapter is intentionally stdlib-only
    so the self-hosted MVP does not need another Python dependency.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        upload_dir: str | None = None,
        timeout_seconds: float = 180,
        max_tokens: int = 256,
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
        self._resolver = ImageResolver(upload_dir)
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.transport = transport or self._post_json

    def run(self, image_storage_key: str) -> AnalysisResult:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"

        errors: list[str] = []
        for i, payload in enumerate(self._build_payloads(image_storage_key), start=1):
            try:
                response = self.transport(
                    f"{self.base_url}/chat/completions",
                    payload,
                    headers,
                    self.timeout_seconds,
                )
                items = self._parse_items(response)
                break
            except RuntimeError as exc:
                errors.append(f"Payload {i}: {exc}")
        else:
            raise RuntimeError(
                f"Inference provider returned no usable response after {len(errors)} attempt(s). "
                f"Errors: {'; '.join(errors)}"
            )

        return AnalysisResult(
            items=items,
            engine=f"openai-compatible:{self.model}",
            structured_output_version="2026-04-home-inference",
        )

    def _sanitize_storage_key(self, key: str) -> str:
        """Validate storage key to prevent prompt injection and path traversal."""
        return self._resolver.sanitize_storage_key(key)

    def _image_data_url(self, image_storage_key: str) -> str | None:
        """Return a base64 data URL for the image, or None if not found / unsafe."""
        return self._resolver.resolve(image_storage_key)

    def _build_payloads(self, image_storage_key: str) -> list[dict[str, Any]]:
        safe_key = self._sanitize_storage_key(image_storage_key)
        return [
            self._build_payload(
                safe_key,
                system_prompt=(
                    "You are DECLuTTER-AI's item detection adapter. "
                    "Return compact valid JSON only. Do not include markdown."
                ),
                user_prompt=(
                    "Analyze this decluttering image and return ONLY JSON with "
                    "an items array. Each item must have label and confidence "
                    "between 0 and 1. Example: "
                    '{"items":[{"label":"book","confidence":0.82}]} '
                    f"Storage key: {safe_key}"
                ),
                include_response_format=True,
            ),
            self._build_payload(
                safe_key,
                system_prompt=(
                    "You identify the visible items in DECLuTTER-AI photos. "
                    "Reply only with a compact JSON object containing an "
                    '"items" array of {label, confidence}.'
                ),
                user_prompt=(
                    "Identify the visible items in this image. Reply only with "
                    'JSON like {"items":[{"label":"book","confidence":0.82}]}.'
                ),
                include_response_format=True,
            ),
            self._build_payload(
                safe_key,
                system_prompt=(
                    "You identify the visible items in DECLuTTER-AI photos. "
                    "Reply only with a compact JSON object containing an "
                    '"items" array of {label, confidence}.'
                ),
                user_prompt=(
                    "Identify the visible items in this image. Reply only with "
                    'JSON like {"items":[{"label":"book","confidence":0.82}]}.'
                ),
                include_response_format=False,
            ),
        ]

    def _build_payload(
        self,
        image_storage_key: str,
        *,
        system_prompt: str,
        user_prompt: str,
        include_response_format: bool,
    ) -> dict[str, Any]:
        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": user_prompt,
            }
        ]

        image_url = self._image_data_url(image_storage_key)
        if image_url:
            user_content.append({"type": "image_url", "image_url": {"url": image_url}})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        if include_response_format:
            payload["response_format"] = {"type": "text"}
        return payload

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
        if not content.strip():
            raise RuntimeError("Inference provider returned empty message content.")

        try:
            parsed = json.loads(_extract_json_object(content))
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


# ---------------------------------------------------------------------------
# Anthropic adapter (Claude Messages API)
# ---------------------------------------------------------------------------


class AnthropicAnalysisAdapter:
    """Structured item detection through Anthropic's Messages API.

    Supports Claude 3/3.5 models with vision (e.g., claude-3-5-sonnet,
    claude-3-opus, claude-3-haiku). Uses the Messages API format with
    base64-encoded image content blocks.
    """

    _API_VERSION = "2023-06-01"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        upload_dir: str | None = None,
        timeout_seconds: float = 180,
        max_tokens: int = 256,
        transport: Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]
        | None = None,
    ) -> None:
        if not base_url.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_BASE_URL is required for Anthropic analysis."
            )
        if not model.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_MODEL is required for Anthropic analysis."
            )

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._resolver = ImageResolver(upload_dir)
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.transport = transport or self._post_json

    def run(self, image_storage_key: str) -> AnalysisResult:
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": self._API_VERSION,
        }
        if self.api_key and self.api_key.strip():
            headers["x-api-key"] = self.api_key.strip()

        errors: list[str] = []
        for i, payload in enumerate(self._build_payloads(image_storage_key), start=1):
            try:
                response = self.transport(
                    f"{self.base_url}/v1/messages",
                    payload,
                    headers,
                    self.timeout_seconds,
                )
                items = self._parse_items(response)
                break
            except RuntimeError as exc:
                errors.append(f"Payload {i}: {exc}")
        else:
            raise RuntimeError(
                f"Anthropic provider returned no usable response after {len(errors)} attempt(s). "
                f"Errors: {'; '.join(errors)}"
            )

        return AnalysisResult(
            items=items,
            engine=f"anthropic:{self.model}",
            structured_output_version="2026-04-anthropic-messages",
        )

    def _build_payloads(self, image_storage_key: str) -> list[dict[str, Any]]:
        image_url = self._resolver.resolve(image_storage_key)
        if not image_url:
            # Fallback: try without image if file is missing (preserves test compatibility)
            image_content: list[dict[str, Any]] = []
        else:
            # Parse data URL: data:image/jpeg;base64,...
            header, b64_data = image_url.split(",", 1)
            media_type = header.replace("data:", "").replace(";base64", "")
            image_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type or "image/jpeg",
                        "data": b64_data,
                    },
                }
            ]

        return [
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": 0,
                "system": (
                    "You are DECLuTTER-AI's item detection adapter. "
                    "Return compact valid JSON only. Do not include markdown. "
                    "Example: {\"items\":[{\"label\":\"book\",\"confidence\":0.82}]}"
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": image_content
                        + [
                            {
                                "type": "text",
                                "text": (
                                    "Analyze this decluttering image and return ONLY JSON "
                                    "with an items array. Each item must have label and "
                                    "confidence between 0 and 1."
                                ),
                            }
                        ],
                    }
                ],
            },
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": 0,
                "system": (
                    "You identify the visible items in DECLuTTER-AI photos. "
                    "Reply only with a compact JSON object containing an "
                    '"items" array of {label, confidence}.'
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": image_content
                        + [
                            {
                                "type": "text",
                                "text": (
                                    "Identify the visible items in this image. "
                                    "Reply only with JSON like "
                                    '{"items":[{"label":"book","confidence":0.82}]}'
                                ),
                            }
                        ],
                    }
                ],
            },
        ]

    @staticmethod
    def _parse_items(response: dict[str, Any]) -> list[DetectedItem]:
        content = response.get("content")
        if not isinstance(content, list) or not content:
            raise RuntimeError("Anthropic provider returned no content blocks.")

        first_block = content[0]
        if not isinstance(first_block, dict):
            raise RuntimeError("Anthropic provider returned an invalid content block.")

        text = first_block.get("text")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Anthropic provider returned empty text content.")

        try:
            parsed = json.loads(_extract_json_object(text))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Anthropic provider returned non-JSON item output.") from exc

        raw_items = parsed.get("items")
        if not isinstance(raw_items, list):
            raise RuntimeError("Anthropic provider JSON must contain an items array.")

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
            raise RuntimeError("Anthropic provider returned no usable detected items.")

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
                f"Anthropic provider returned HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Anthropic provider request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Ollama native adapter (uses /api/generate, not the OpenAI-compatible wrapper)
# ---------------------------------------------------------------------------


class OllamaAnalysisAdapter:
    """Structured item detection through Ollama's native API.

    This uses the ``/api/generate`` endpoint directly rather than the
    OpenAI-compatible ``/v1/chat/completions`` wrapper. Useful when you want
    to avoid loading the OpenAI compatibility layer or need Ollama-specific
    features like ``format: json``.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        upload_dir: str | None = None,
        timeout_seconds: float = 180,
        max_tokens: int = 256,
        transport: Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]
        | None = None,
    ) -> None:
        if not base_url.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_BASE_URL is required for Ollama analysis."
            )
        if not model.strip():
            raise RuntimeError(
                "DECLUTTER_INFERENCE_MODEL is required for Ollama analysis."
            )

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._resolver = ImageResolver(upload_dir)
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.transport = transport or self._post_json

    def run(self, image_storage_key: str) -> AnalysisResult:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"

        errors: list[str] = []
        for i, payload in enumerate(self._build_payloads(image_storage_key), start=1):
            try:
                response = self.transport(
                    f"{self.base_url}/api/generate",
                    payload,
                    headers,
                    self.timeout_seconds,
                )
                items = self._parse_items(response)
                break
            except RuntimeError as exc:
                errors.append(f"Payload {i}: {exc}")
        else:
            raise RuntimeError(
                f"Ollama provider returned no usable response after {len(errors)} attempt(s). "
                f"Errors: {'; '.join(errors)}"
            )

        return AnalysisResult(
            items=items,
            engine=f"ollama:{self.model}",
            structured_output_version="2026-04-ollama-native",
        )

    def _build_payloads(self, image_storage_key: str) -> list[dict[str, Any]]:
        image_url = self._resolver.resolve(image_storage_key)
        images: list[str] = []
        if image_url:
            # Strip the data:...;base64, prefix to get raw base64
            images = [image_url.split(",", 1)[1]]

        system = (
            "You are DECLuTTER-AI's item detection adapter. "
            "Return compact valid JSON only. Do not include markdown. "
            "Example: {\"items\":[{\"label\":\"book\",\"confidence\":0.82}]}"
        )

        return [
            {
                "model": self.model,
                "system": system,
                "prompt": (
                    "Analyze this decluttering image and return ONLY JSON with "
                    "an items array. Each item must have label and confidence "
                    "between 0 and 1."
                ),
                "images": images,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": self.max_tokens,
                },
            },
            {
                "model": self.model,
                "system": system,
                "prompt": (
                    "Identify the visible items in this image. Reply only with "
                    "JSON like {\"items\":[{\"label\":\"book\",\"confidence\":0.82}]}"
                ),
                "images": images,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": self.max_tokens,
                },
            },
        ]

    @staticmethod
    def _parse_items(response: dict[str, Any]) -> list[DetectedItem]:
        response_text = response.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise RuntimeError("Ollama provider returned empty response.")

        try:
            parsed = json.loads(_extract_json_object(response_text))
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama provider returned non-JSON item output.") from exc

        raw_items = parsed.get("items")
        if not isinstance(raw_items, list):
            raise RuntimeError("Ollama provider JSON must contain an items array.")

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
            raise RuntimeError("Ollama provider returned no usable detected items.")

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
                f"Ollama provider returned HTTP {exc.code}: {detail[:500]}"
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama provider request failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def _resolve_inference_config() -> dict[str, Any]:
    """Gather inference configuration from environment variables."""
    return {
        "base_url": (
            os.getenv("DECLUTTER_INFERENCE_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("LMSTUDIO_BASE_URL")
            or os.getenv("LM_STUDIO_BASE_URL")
            or os.getenv("ANTHROPIC_BASE_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or ""
        ),
        "model": (
            os.getenv("DECLUTTER_INFERENCE_MODEL")
            or os.getenv("OPENAI_MODEL")
            or os.getenv("LMSTUDIO_MODEL")
            or os.getenv("LM_STUDIO_MODEL")
            or os.getenv("ANTHROPIC_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or ""
        ),
        "api_key": (
            os.getenv("DECLUTTER_INFERENCE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("LMSTUDIO_API_KEY")
            or os.getenv("LM_STUDIO_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OLLAMA_API_KEY")
        ),
        "timeout_seconds": float(os.getenv("DECLUTTER_INFERENCE_TIMEOUT_SECONDS", "180")),
        "max_tokens": int(os.getenv("DECLUTTER_INFERENCE_MAX_TOKENS", "256")),
    }


def create_analysis_adapter_from_env() -> AnalysisAdapter:
    """Instantiate the appropriate analysis adapter based on env configuration.

    Supported providers:

    * ``mock`` — deterministic mock detections (default)
    * ``openai`` / ``openai-compatible`` / ``groq`` / ``together`` /
      ``fireworks`` / ``cerebras`` / ``home`` / ``lmstudio`` — any
      OpenAI-compatible ``/v1/chat/completions`` endpoint
    * ``anthropic`` / ``claude`` — Anthropic Messages API
    * ``ollama-native`` / ``ollama_direct`` — Ollama ``/api/generate`` endpoint

    The OpenAI-compatible adapter is the default for any provider name that is
    not explicitly mapped to another adapter class. This means new providers
    that expose an OpenAI-compatible API work out of the box.
    """
    provider = (
        os.getenv("DECLUTTER_ANALYSIS_PROVIDER")
        or os.getenv("DECLUTTER_MODEL_PROVIDER")
        or "mock"
    ).strip().lower()

    if provider == "mock":
        return MockStructuredAnalysisAdapter()

    config = _resolve_inference_config()

    # Anthropic / Claude
    if provider in {"anthropic", "claude"}:
        # Anthropic default base URL if none provided
        if not config["base_url"]:
            config["base_url"] = "https://api.anthropic.com"
        return AnthropicAnalysisAdapter(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            timeout_seconds=config["timeout_seconds"],
            max_tokens=config["max_tokens"],
        )

    # Ollama native API (not the OpenAI-compatible wrapper)
    if provider in {"ollama-native", "ollama_native", "ollama-direct", "ollama_direct"}:
        if not config["base_url"]:
            config["base_url"] = "http://127.0.0.1:11434"
        return OllamaAnalysisAdapter(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            timeout_seconds=config["timeout_seconds"],
            max_tokens=config["max_tokens"],
        )

    # OpenAI-compatible catch-all (OpenAI, Groq, Together, LM Studio,
    # Azure OpenAI, Fireworks, Cerebras, Ollama's /v1 wrapper, etc.)
    openai_compatible_providers = {
        "openai",
        "openai_compatible",
        "openai-compatible",
        "groq",
        "together",
        "togetherai",
        "together-ai",
        "fireworks",
        "fireworks-ai",
        "fireworks_ai",
        "cerebras",
        "home",
        "home_inference",
        "home-inference",
        "lmstudio",
        "lm-studio",
    }
    if provider in openai_compatible_providers:
        # Default LM Studio URL when provider name hints at it
        if "lm" in provider and not config["base_url"]:
            config["base_url"] = "http://127.0.0.1:1234/v1"
        if not config["base_url"]:
            config["base_url"] = "https://api.openai.com/v1"
        return OpenAICompatibleAnalysisAdapter(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            timeout_seconds=config["timeout_seconds"],
            max_tokens=config["max_tokens"],
        )

    # Ultimate fallback: if a base_url and model are configured, treat as
    # OpenAI-compatible even if the provider name is unrecognized.
    if config["base_url"] and config["model"]:
        return OpenAICompatibleAnalysisAdapter(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            timeout_seconds=config["timeout_seconds"],
            max_tokens=config["max_tokens"],
        )

    return MockStructuredAnalysisAdapter()


# ---------------------------------------------------------------------------
# JSON extraction helper (shared across all adapters)
# ---------------------------------------------------------------------------


def _extract_json_object(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        if first_newline != -1:
            last_fence = stripped.rfind("```")
            if last_fence > first_newline:
                inner = stripped[first_newline:last_fence].strip()
                start = inner.find("{")
                end = inner.rfind("}")
                if start != -1 and end > start:
                    return inner[start : end + 1]

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]

    return stripped
