import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routes.a2a import router as a2a_router
from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.launch import router as launch_router
from api.routes.listing_drafts import router as listing_router
from api.routes.marketplace_ebay import router as ebay_router
from api.routes.mcp import router as mcp_router
from api.routes.operator import router as operator_router
from api.routes.public_listings import router as public_listings_router
from api.routes.seller import router as seller_router
from api.routes.sessions import router as sessions_router
from api.routes.user_data import router as user_data_router
from api.routes.valuation import router as valuation_router
from core.settings import Settings
from middleware.rate_limit import RateLimitMiddleware
from middleware.request_logging import RequestLoggingMiddleware
from middleware.request_size import RequestSizeLimitMiddleware
from security.dependencies import require_firebase_protection

logger = logging.getLogger("declutter.request")


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def create_app() -> FastAPI:
    api = FastAPI(title="DECLuTTER-AI API", version="0.1.0")

    # Middleware order: logging (outer) -> size limit -> rate limit -> CORS -> routes
    api.add_middleware(RequestLoggingMiddleware)
    api.add_middleware(RequestSizeLimitMiddleware, max_bytes=10 * 1024 * 1024)
    if os.getenv('DECLUTTER_RATE_LIMIT_DISABLED', '').lower() not in {'1', 'true', 'yes'}:
        api.add_middleware(RateLimitMiddleware)

    cors_origins = Settings.cors_allow_origins()
    if cors_origins:
        api.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @api.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "correlation_id": _correlation_id(request)},
            headers=getattr(exc, "headers", None) or {},
        )

    @api.exception_handler(KeyError)
    async def keyerror_handler(request: Request, exc: KeyError) -> JSONResponse:
        logger.warning("KeyError at %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "detail": str(exc),
                "correlation_id": _correlation_id(request),
            },
        )

    @api.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
        logger.error("RuntimeError at %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service unavailable",
                "detail": str(exc),
                "correlation_id": _correlation_id(request),
            },
        )

    @api.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception at %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "correlation_id": _correlation_id(request),
            },
        )

    api.include_router(health_router)
    api.include_router(launch_router)
    api.include_router(public_listings_router)
    api.include_router(operator_router)

    # Seller routes are open by default for the public beta.
    # Set DECLUTTER_SELLER_AUTH_MODE=protected to require Firebase auth.
    seller_protected = (
        [Depends(require_firebase_protection)]
        if os.getenv('DECLUTTER_SELLER_AUTH_MODE', '').strip().lower() == 'protected'
        else []
    )
    api.include_router(seller_router, dependencies=seller_protected)

    protected = [Depends(require_firebase_protection)]
    api.include_router(analysis_router, dependencies=protected)
    api.include_router(sessions_router, dependencies=protected)
    api.include_router(valuation_router, dependencies=protected)
    api.include_router(listing_router, dependencies=protected)
    api.include_router(ebay_router, dependencies=protected)
    api.include_router(mcp_router, dependencies=protected)
    api.include_router(a2a_router, dependencies=protected)
    api.include_router(user_data_router, dependencies=protected)

    return api


app = create_app()
