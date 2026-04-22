from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image


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


class LocalImageStorageAdapter:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def put(self, payload: bytes, extension: str) -> str:
        storage_key = f"intake/{uuid4().hex}.{extension}"
        destination = self.base_dir / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return storage_key


class ImageIntakeService:
    def __init__(
        self,
        storage: LocalImageStorageAdapter | None = None,
        scanner: MalwareScanner | None = None,
    ) -> None:
        self.storage = storage or LocalImageStorageAdapter()
        self.scanner = scanner or NoopMalwareScanner()

    async def intake(self, image: UploadFile) -> ImageIntakeResult:
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

        sanitized_payload, extension = self._strip_metadata(raw_payload, image.content_type)
        self.scanner.scan(sanitized_payload)
        storage_key = self.storage.put(sanitized_payload, extension)

        return ImageIntakeResult(
            storage_key=storage_key,
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
