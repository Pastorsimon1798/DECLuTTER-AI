from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException, Request, status

from security.firebase import FirebaseTokenVerifier


@lru_cache(maxsize=1)
def get_firebase_verifier() -> FirebaseTokenVerifier:
    return FirebaseTokenVerifier()


def require_firebase_protection(
    request: Request,
    authorization: str | None = Header(default=None),
    x_firebase_appcheck: str | None = Header(default=None),
    verifier: FirebaseTokenVerifier = Depends(get_firebase_verifier),
) -> None:
    if verifier.settings.auth_mode == "off":
        request.state.user_claims = {"uid": "local-dev"}
        request.state.app_claims = {"app_id": "local-dev"}
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    if verifier.settings.auth_mode != "shared_token" and not x_firebase_appcheck:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Firebase App Check header.",
        )

    id_token = authorization.removeprefix("Bearer ").strip()

    try:
        user_claims = verifier.verify_id_token(id_token)
        app_check_token = x_firebase_appcheck.strip() if x_firebase_appcheck else ""
        app_claims = verifier.verify_app_check_token(app_check_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please check your credentials and try again.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Please try again later.",
        ) from exc

    request.state.user_claims = user_claims
    request.state.app_claims = app_claims
