from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


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

    def __init__(self, base_dir: str | None = None, expires_in_seconds: int = 900) -> None:
        self.base_dir = Path(base_dir or os.getenv("DECLUTTER_UPLOAD_DIR", "/tmp/declutter_ai_uploads"))
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
