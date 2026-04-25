from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4


class ImageStorageAdapter(Protocol):
    def put(self, payload: bytes, extension: str, storage_key: str | None = None) -> str:
        """Persist image bytes and return a storage key."""


def _sanitize_storage_key(key: str | None, default_extension: str) -> str:
    if not key:
        return f"intake/{uuid4().hex}.{default_extension}"
    sanitized = key.strip()
    if ".." in sanitized or not all(c.isalnum() or c in "._-/" for c in sanitized):
        raise RuntimeError("Invalid characters in storage key.")
    return sanitized


class LocalImageStorageAdapter:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(
            base_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads")
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def put(self, payload: bytes, extension: str, storage_key: str | None = None) -> str:
        key = _sanitize_storage_key(storage_key, extension)
        destination = self.base_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return key


class S3ImageStorageAdapter:
    def __init__(
        self,
        bucket: str | None = None,
        key_prefix: str | None = None,
        region_name: str | None = None,
    ) -> None:
        self.bucket = bucket or os.getenv("DECLUTTER_S3_BUCKET", "")
        self.key_prefix = (
            key_prefix or os.getenv("DECLUTTER_S3_PREFIX", "intake")
        ).strip("/")
        self.region_name = region_name or os.getenv("AWS_REGION")

        if not self.bucket:
            raise RuntimeError(
                "DECLUTTER_S3_BUCKET is required when storage backend is s3."
            )

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError(
                "S3 storage backend requires boto3 to be installed."
            ) from exc

        self.client = boto3.client("s3", region_name=self.region_name)

    def put(self, payload: bytes, extension: str, storage_key: str | None = None) -> str:
        key = _sanitize_storage_key(storage_key, f"{self.key_prefix}/{uuid4().hex}.{extension}")
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload,
            ContentType=f"image/{extension}",
        )
        return key


def create_storage_adapter_from_env() -> ImageStorageAdapter:
    backend = os.getenv("DECLUTTER_STORAGE_BACKEND", "local").strip().lower()

    if backend == "local":
        return LocalImageStorageAdapter()

    if backend == "s3":
        return S3ImageStorageAdapter()

    raise RuntimeError(f"Unsupported DECLUTTER_STORAGE_BACKEND: {backend}")


@dataclass(frozen=True)
class UploadSession:
    storage_key: str
    upload_url: str
    required_headers: dict[str, str]
    expires_in_seconds: int


class LocalSignedUploadAdapter:
    """WP4 hardening scaffold for signed-upload style flow.

    This local implementation emulates a signed URL by providing a `file://`
    destination path. Cloud adapters can implement the same contract later.
    """

    def __init__(
        self,
        base_dir: str | None = None,
        expires_in_seconds: int = 900,
    ) -> None:
        self.base_dir = Path(
            base_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads")
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.expires_in_seconds = expires_in_seconds

    def create_upload_session(self, extension: str = "jpg") -> UploadSession:
        storage_key = f"intake/{uuid4().hex}.{extension}"
        destination = self.base_dir / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)

        return UploadSession(
            storage_key=storage_key,
            upload_url=f"file://{destination}",
            required_headers={"x-declutter-upload-token": "local-dev-token"},
            expires_in_seconds=self.expires_in_seconds,
        )
