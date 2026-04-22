from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FirebaseSecuritySettings:
    auth_mode: str
    accepted_id_token: str
    accepted_app_check_token: str

    @classmethod
    def from_env(cls) -> "FirebaseSecuritySettings":
        return cls(
            auth_mode=os.getenv("DECLUTTER_AUTH_MODE", "scaffold").strip().lower(),
            accepted_id_token=os.getenv("DECLUTTER_TEST_ID_TOKEN", "test-user-token"),
            accepted_app_check_token=os.getenv(
                "DECLUTTER_TEST_APP_CHECK_TOKEN", "test-app-check-token"
            ),
        )


class FirebaseTokenVerifier:
    """Small verification adapter used by request dependencies.

    Modes:
    - off: skip all checks (local development only).
    - scaffold (default): validates fixed test tokens.
    - strict: reserved for real Firebase Admin SDK integration in WP3 hardening.
    """

    def __init__(self, settings: FirebaseSecuritySettings | None = None) -> None:
        self.settings = settings or FirebaseSecuritySettings.from_env()

    def verify_id_token(self, token: str) -> dict[str, str]:
        if self.settings.auth_mode == "off":
            return {"uid": "local-dev"}

        if self.settings.auth_mode == "scaffold":
            if token != self.settings.accepted_id_token:
                raise ValueError("Invalid Firebase ID token.")
            return {"uid": "scaffold-user"}

        raise ValueError("Strict Firebase auth mode is not configured yet.")

    def verify_app_check_token(self, token: str) -> dict[str, str]:
        if self.settings.auth_mode == "off":
            return {"app_id": "local-dev"}

        if self.settings.auth_mode == "scaffold":
            if token != self.settings.accepted_app_check_token:
                raise ValueError("Invalid Firebase App Check token.")
            return {"app_id": "scaffold-app"}

        raise ValueError("Strict Firebase App Check mode is not configured yet.")
