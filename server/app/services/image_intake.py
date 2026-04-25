from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from services.storage_adapter import ImageStorageAdapter, LocalImageStorageAdapter


MAX_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@dataclass(frozen=True)
class ImageIntakeResult:
    storage_key: str
    content_type: str
    original_size_bytes: int
    sanitized_size_bytes: int


class MalwareScanner:
    """Interface for malware scanning hooks in WP4 hardening."""

    def scan(self, payload: bytes) -> None:
        raise NotImplementedError


class NoopMalwareScanner(MalwareScanner):
    def scan(self, payload: bytes) -> None:
        _ = payload


class ImageIntakeService:
    def __init__(
        self,
        storage: ImageStorageAdapter | None = None,
        scanner: MalwareScanner | None = None,
    ) -> None:
        self.storage = storage or LocalImageStorageAdapter()
        self.scanner = scanner or NoopMalwareScanner()

    async def intake(self, image: UploadFile, storage_key: str | None = None) -> ImageIntakeResult:
        if image.content_type not in SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported image content type.",
            )

        raw_payload = await image.read()
        if len(raw_payload) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image exceeds the 10MB upload limit.",
            )

        try:
            sanitized_payload, extension = await asyncio.to_thread(
                self._strip_metadata,
                raw_payload,
                image.content_type,
            )
        except (OSError, UnidentifiedImageError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed or unreadable image upload.",
            ) from exc

        self.scanner.scan(sanitized_payload)
        final_key = self.storage.put(sanitized_payload, extension, storage_key)

        return ImageIntakeResult(
            storage_key=final_key,
            content_type=image.content_type,
            original_size_bytes=len(raw_payload),
            sanitized_size_bytes=len(sanitized_payload),
        )

    @staticmethod
    def _strip_metadata(raw_payload: bytes, content_type: str) -> tuple[bytes, str]:
        output = io.BytesIO()

        with Image.open(io.BytesIO(raw_payload)) as parsed:
            sanitized = parsed.copy()

            if content_type == "image/png":
                sanitized.save(output, format="PNG")
                return output.getvalue(), "png"

            if content_type == "image/webp":
                sanitized.save(output, format="WEBP", quality=95)
                return output.getvalue(), "webp"

            sanitized = sanitized.convert("RGB")
            sanitized.save(output, format="JPEG", quality=95)
            return output.getvalue(), "jpg"
