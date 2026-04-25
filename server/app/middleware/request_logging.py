"""Structured request logging middleware with correlation IDs."""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with a correlation ID and timing info."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.time() - start_time) * 1000
            self._log(request, 500, duration_ms, correlation_id)
            raise

        duration_ms = (time.time() - start_time) * 1000
        self._log(request, response.status_code, duration_ms, correlation_id)
        response.headers["x-correlation-id"] = correlation_id
        return response

    @staticmethod
    def _log(request: Request, status_code: int, duration_ms: float, correlation_id: str) -> None:
        # Use stdlib logging if available, otherwise print
        import logging

        logger = logging.getLogger("declutter.request")
        logger.info(
            "method=%s path=%s status=%d duration_ms=%.2f correlation_id=%s client_ip=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            correlation_id,
            getattr(request.client, "host", "unknown") if request.client else "unknown",
        )
