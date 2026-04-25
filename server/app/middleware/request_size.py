"""Request size limit middleware."""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects requests whose Content-Length exceeds a global maximum."""

    def __init__(self, app, max_bytes: int = 10 * 1024 * 1024) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                return Response(
                    content='{"detail":"Invalid Content-Length header."}',
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                )
            if length > self.max_bytes:
                return Response(
                    content=f'"detail":"Request body exceeds {self.max_bytes // (1024 * 1024)}MB limit."',
                    status_code=413,
                    headers={"Content-Type": "application/json"},
                )
        return await call_next(request)
