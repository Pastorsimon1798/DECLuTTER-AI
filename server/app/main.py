from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.a2a import router as a2a_router
from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.launch import router as launch_router
from api.routes.listing_drafts import router as listing_router
from api.routes.marketplace_ebay import router as ebay_router
from api.routes.mcp import router as mcp_router
from api.routes.public_listings import router as public_listings_router
from api.routes.sessions import router as sessions_router
from api.routes.user_data import router as user_data_router
from api.routes.valuation import router as valuation_router
from core.settings import Settings
from security.dependencies import require_firebase_protection


def create_app() -> FastAPI:
    api = FastAPI(title="DECLuTTER-AI API", version="0.1.0")

    cors_origins = Settings.cors_allow_origins()
    if cors_origins:
        api.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    api.include_router(health_router)
    api.include_router(launch_router)
    api.include_router(public_listings_router)

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
