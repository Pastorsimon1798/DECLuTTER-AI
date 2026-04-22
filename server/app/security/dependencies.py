from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from security.firebase import FirebaseTokenVerifier

_verifier = FirebaseTokenVerifier()


def require_firebase_protection(
    request: Request,
    authorization: str | None = Header(default=None),
    x_firebase_appcheck: str | None = Header(default=None),
) -> None:
    if _verifier.settings.auth_mode == "off":
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    if not x_firebase_appcheck:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Firebase App Check header.",
        )

    id_token = authorization.removeprefix("Bearer ").strip()

    try:
        user_claims = _verifier.verify_id_token(id_token)
        app_claims = _verifier.verify_app_check_token(x_firebase_appcheck.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    request.state.user_claims = user_claims
    request.state.app_claims = app_claims
