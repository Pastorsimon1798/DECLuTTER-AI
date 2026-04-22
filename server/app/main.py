from fastapi import Depends, FastAPI

from api.routes.a2a import router as a2a_router
from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.listing_drafts import router as listing_router
from api.routes.marketplace_ebay import router as ebay_router
from api.routes.mcp import router as mcp_router
from api.routes.public_listings import router as public_listings_router
from api.routes.user_data import router as user_data_router
from api.routes.valuation import router as valuation_router
from security.dependencies import require_firebase_protection

app = FastAPI(title="DECLuTTER-AI API", version="0.1.0")

app.include_router(health_router)
app.include_router(public_listings_router)

protected = [Depends(require_firebase_protection)]
app.include_router(analysis_router, dependencies=protected)
app.include_router(valuation_router, dependencies=protected)
app.include_router(listing_router, dependencies=protected)
app.include_router(ebay_router, dependencies=protected)
app.include_router(mcp_router, dependencies=protected)
app.include_router(a2a_router, dependencies=protected)
app.include_router(user_data_router, dependencies=protected)
