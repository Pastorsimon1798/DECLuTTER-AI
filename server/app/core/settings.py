from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeReadiness:
    firebase_admin_configured: bool
    cloud_storage_configured: bool
    multimodal_model_configured: bool
    ebay_api_configured: bool

    @property
    def ready_for_production(self) -> bool:
        return (
            self.firebase_admin_configured
            and self.cloud_storage_configured
            and self.multimodal_model_configured
            and self.ebay_api_configured
        )


class Settings:
    _PLACEHOLDER_VALUES = {
        "...",
        "bucket",
        "demo-project",
        "id",
        "launch-model-provider",
        "mock-model",
        "secret",
        "your-ebay-client-id",
        "your-ebay-client-secret",
        "your-firebase-project-id",
        "your-private-upload-bucket",
    }
    _PLACEHOLDER_PREFIXES = (
        "replace-with-",
        "todo-",
        "your-",
    )

    @staticmethod
    def readiness() -> RuntimeReadiness:
        return RuntimeReadiness(
            firebase_admin_configured=Settings._configured_env("FIREBASE_PROJECT_ID"),
            cloud_storage_configured=Settings._cloud_storage_configured(),
            multimodal_model_configured=Settings._configured_env(
                "DECLUTTER_MODEL_PROVIDER"
            ),
            ebay_api_configured=bool(
                Settings._configured_env("EBAY_CLIENT_ID")
                and Settings._configured_env("EBAY_CLIENT_SECRET")
            ),
        )

    @staticmethod
    def _cloud_storage_configured() -> bool:
        storage_backend = os.getenv("DECLUTTER_STORAGE_BACKEND", "local").strip().lower()
        return storage_backend == "s3" and Settings._configured_env(
            "DECLUTTER_S3_BUCKET"
        )

    @staticmethod
    def _configured_env(name: str) -> bool:
        value = os.getenv(name)
        if value is None:
            return False

        normalized = value.strip().lower()
        if not normalized:
            return False

        if normalized in Settings._PLACEHOLDER_VALUES:
            return False

        if normalized.startswith(Settings._PLACEHOLDER_PREFIXES):
            return False

        return "example" not in normalized and "placeholder" not in normalized

    @staticmethod
    def cors_allow_origins() -> list[str]:
        raw_origins = os.getenv("DECLUTTER_CORS_ALLOW_ORIGINS", "")
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
