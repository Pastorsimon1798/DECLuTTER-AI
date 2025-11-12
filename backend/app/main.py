"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Integrated Mutual Aid Platform - Combining Discovery, Matching, Coordination, and Community",
    version="1.0.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CommunityCircle API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "version": "1.0.0",
    }


# Import API routers
from app.api import auth, posts, matches, organizations, shifts

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(posts.router, prefix=f"{settings.API_V1_PREFIX}/posts", tags=["Posts"])
app.include_router(matches.router, prefix=f"{settings.API_V1_PREFIX}/matches", tags=["Matches"])
app.include_router(organizations.router, prefix=f"{settings.API_V1_PREFIX}/organizations", tags=["Organizations"])
app.include_router(shifts.router, prefix=f"{settings.API_V1_PREFIX}/shifts", tags=["Shifts"])


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions"""
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
