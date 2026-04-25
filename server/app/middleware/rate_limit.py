"""Simple in-memory rate-limiting middleware.

Production deployments should replace this with a Redis-backed store
(e.g. SlowAPI) so limits are shared across workers.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiter keyed by client IP + path prefix.

    Defaults:
    - Global: 60 requests / 60 seconds
    - /analysis/intake: 10 requests / 60 seconds
    """

    def __init__(
        self,
        app,
        default_limit: int = 60,
        window_seconds: int = 60,
        path_limits: dict[str, tuple[int, int]] | None = None,
    ) -> None:
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.path_limits = path_limits or {"/analysis/intake": (10, 60)}
        # _state[client_ip][window_start] = count
        self._state: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = self._client_ip(request)
        now = int(time.time())
        current_window = now // self.window_seconds

        limit, _window = self._limit_for_path(request.url.path)

        # Clean old windows for this IP (simple GC)
        self._gc(client_ip, current_window)

        self._state[client_ip][current_window] += 1
        if self._state[client_ip][current_window] > limit:
            return Response(
                content='{"detail":"Rate limit exceeded."}',
                status_code=429,
                headers={"Content-Type": "application/json"},
            )

        return await call_next(request)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _limit_for_path(self, path: str) -> tuple[int, int]:
        for prefix, (limit, window) in self.path_limits.items():
            if path.startswith(prefix):
                return limit, window
        return self.default_limit, self.window_seconds

    def _gc(self, client_ip: str, current_window: int) -> None:
        # Keep only the current window to limit memory growth
        windows = list(self._state[client_ip].keys())
        for w in windows:
            if w < current_window:
                del self._state[client_ip][w]
