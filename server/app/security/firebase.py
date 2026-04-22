from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FirebaseSecuritySettings:
    auth_mode: str
    accepted_id_token: str
    accepted_app_check_token: str
    shared_access_token: str

    @classmethod
    def from_env(cls) -> "FirebaseSecuritySettings":
        return cls(
            auth_mode=os.getenv("DECLUTTER_AUTH_MODE", "strict").strip().lower(),
            accepted_id_token=os.getenv("DECLUTTER_TEST_ID_TOKEN", ""),
            accepted_app_check_token=os.getenv("DECLUTTER_TEST_APP_CHECK_TOKEN", ""),
            shared_access_token=os.getenv("DECLUTTER_SHARED_ACCESS_TOKEN", ""),
        )


class FirebaseTokenVerifier:
    """Verification adapter for Firebase Auth + App Check.

    Supported modes:
    - off: bypass validation entirely (local-only).
    - shared_token: one shared bearer token for self-hosted MVP deployments.
    - scaffold: fixed token checks for deterministic tests/dev.
    - strict: uses Firebase Admin SDK token verification.
    """

    def __init__(self, settings: FirebaseSecuritySettings | None = None) -> None:
        self.settings = settings or FirebaseSecuritySettings.from_env()

    def verify_id_token(self, token: str) -> dict[str, Any]:
        if self.settings.auth_mode == "off":
            return {"uid": "local-dev"}

        if self.settings.auth_mode == "shared_token":
            self._require_scaffold_token(
                self.settings.shared_access_token,
                "DECLUTTER_SHARED_ACCESS_TOKEN",
            )
            if token != self.settings.shared_access_token:
                raise ValueError("Invalid shared access token.")
            return {"uid": "self-hosted-user"}

        if self.settings.auth_mode == "scaffold":
            self._require_scaffold_token(
                self.settings.accepted_id_token,
                "DECLUTTER_TEST_ID_TOKEN",
            )
            if token != self.settings.accepted_id_token:
                raise ValueError("Invalid Firebase ID token.")
            return {"uid": "scaffold-user"}

        if self.settings.auth_mode == "strict":
            return self._verify_id_token_strict(token)

        raise RuntimeError(f"Unsupported DECLUTTER_AUTH_MODE: {self.settings.auth_mode}")

    def verify_app_check_token(self, token: str) -> dict[str, Any]:
        if self.settings.auth_mode == "off":
            return {"app_id": "local-dev"}

        if self.settings.auth_mode == "shared_token":
            return {"app_id": "self-hosted-mvp"}

        if self.settings.auth_mode == "scaffold":
            self._require_scaffold_token(
                self.settings.accepted_app_check_token,
                "DECLUTTER_TEST_APP_CHECK_TOKEN",
            )
            if token != self.settings.accepted_app_check_token:
                raise ValueError("Invalid Firebase App Check token.")
            return {"app_id": "scaffold-app"}

        if self.settings.auth_mode == "strict":
            return self._verify_app_check_token_strict(token)

        raise RuntimeError(f"Unsupported DECLUTTER_AUTH_MODE: {self.settings.auth_mode}")

    @staticmethod
    def _require_scaffold_token(token: str, env_name: str) -> None:
        if not token:
            raise RuntimeError(
                f"{env_name} must be set when DECLUTTER_AUTH_MODE=scaffold."
            )

    @staticmethod
    def _verify_id_token_strict(token: str) -> dict[str, Any]:
        try:
            import firebase_admin
            from firebase_admin import auth
        except ImportError as exc:
            raise RuntimeError(
                "Strict auth mode requires firebase-admin to be installed."
            ) from exc

        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
            except ValueError as exc:
                raise RuntimeError("Failed to initialize Firebase Admin app.") from exc

        try:
            claims = auth.verify_id_token(token, check_revoked=True)
        except Exception as exc:  # pragma: no cover - delegated SDK behavior
            raise ValueError("Invalid Firebase ID token.") from exc

        return dict(claims)

    @staticmethod
    def _verify_app_check_token_strict(token: str) -> dict[str, Any]:
        try:
            import firebase_admin
            from firebase_admin import app_check
        except ImportError as exc:
            raise RuntimeError(
                "Strict auth mode requires firebase-admin to be installed."
            ) from exc

        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
            except ValueError as exc:
                raise RuntimeError("Failed to initialize Firebase Admin app.") from exc

        try:
            claims = app_check.verify_token(token)
        except Exception as exc:  # pragma: no cover - delegated SDK behavior
            raise ValueError("Invalid Firebase App Check token.") from exc

        return dict(claims)
