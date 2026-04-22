from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeReadiness:
    shared_token_auth_configured: bool
    local_upload_storage_configured: bool
    sqlite_session_store_configured: bool
    home_inference_configured: bool
    firebase_admin_configured: bool
    cloud_storage_configured: bool
    multimodal_model_configured: bool
    ebay_api_configured: bool

    @property
    def self_hosted_mvp_ready(self) -> bool:
        return (
            self.shared_token_auth_configured
            and self.local_upload_storage_configured
            and self.sqlite_session_store_configured
        )

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
            shared_token_auth_configured=Settings._shared_token_auth_configured(),
            local_upload_storage_configured=Settings._local_upload_storage_configured(),
            sqlite_session_store_configured=Settings._sqlite_session_store_configured(),
            home_inference_configured=Settings._home_inference_configured(),
            firebase_admin_configured=Settings._configured_env("FIREBASE_PROJECT_ID"),
            cloud_storage_configured=Settings._cloud_storage_configured(),
            multimodal_model_configured=Settings._configured_env(
                "DECLUTTER_MODEL_PROVIDER"
            )
            or Settings._home_inference_configured(),
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
    def _shared_token_auth_configured() -> bool:
        auth_mode = os.getenv("DECLUTTER_AUTH_MODE", "strict").strip().lower()
        return auth_mode == "shared_token" and Settings._configured_env(
            "DECLUTTER_SHARED_ACCESS_TOKEN"
        )

    @staticmethod
    def _local_upload_storage_configured() -> bool:
        storage_backend = os.getenv("DECLUTTER_STORAGE_BACKEND", "local").strip().lower()
        if storage_backend != "local":
            return False

        upload_dir = os.getenv("DECLUTTER_UPLOAD_DIR", "")
        return Settings._configured_path(upload_dir)

    @staticmethod
    def _sqlite_session_store_configured() -> bool:
        return Settings._configured_path(os.getenv("DECLUTTER_SESSION_DB_PATH", ""))

    @staticmethod
    def _home_inference_configured() -> bool:
        provider = (
            os.getenv("DECLUTTER_ANALYSIS_PROVIDER")
            or os.getenv("DECLUTTER_MODEL_PROVIDER")
            or ""
        ).strip().lower()
        if provider not in {
            "home",
            "home_inference",
            "home-inference",
            "lmstudio",
            "lm-studio",
            "openai",
            "openai_compatible",
            "openai-compatible",
        }:
            return False

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
        return Settings._configured_env_value(base_url) and Settings._configured_env_value(
            model
        )

    @staticmethod
    def _configured_env(name: str) -> bool:
        value = os.getenv(name)
        return Settings._configured_env_value(value)

    @staticmethod
    def _configured_env_value(value: str | None) -> bool:
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
    def _configured_path(value: str) -> bool:
        normalized = value.strip()
        if not normalized:
            return False

        lowered = normalized.lower()
        if "example" in lowered or "placeholder" in lowered:
            return False

        return lowered not in {
            "/tmp/declutter_ai_uploads",
            "/tmp/declutter_ai_sessions.sqlite3",
        }

    @staticmethod
    def cors_allow_origins() -> list[str]:
        raw_origins = os.getenv("DECLUTTER_CORS_ALLOW_ORIGINS", "")
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
