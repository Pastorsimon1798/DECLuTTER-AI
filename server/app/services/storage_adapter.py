from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4


class ImageStorageAdapter(Protocol):
    def put(self, payload: bytes, extension: str) -> str:
        """Persist image bytes and return storage key."""


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


class S3ImageStorageAdapter:
    def __init__(
        self,
        bucket: str | None = None,
        key_prefix: str | None = None,
        region_name: str | None = None,
    ) -> None:
        self.bucket = bucket or os.getenv("DECLUTTER_S3_BUCKET", "")
        self.key_prefix = (key_prefix or os.getenv("DECLUTTER_S3_PREFIX", "intake")).strip("/")
        self.region_name = region_name or os.getenv("AWS_REGION")

        if not self.bucket:
            raise RuntimeError("DECLUTTER_S3_BUCKET is required when storage backend is s3.")

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("S3 storage backend requires boto3 to be installed.") from exc

        self.client = boto3.client("s3", region_name=self.region_name)

    def put(self, payload: bytes, extension: str) -> str:
        key = f"{self.key_prefix}/{uuid4().hex}.{extension}"
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
