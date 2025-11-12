"""Tasks for resource cache management"""
from celery import shared_task
from datetime import datetime
from sqlalchemy import select

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.resource import ResourceListing


@celery_app.task(name="app.tasks.cache.refresh_expired_resources")
def refresh_expired_resources():
    """Refresh expired resource cache entries"""
    import asyncio
    asyncio.run(refresh_expired_resources_async())


async def refresh_expired_resources_async():
    """Async implementation of cache refresh"""
    async with AsyncSessionLocal() as db:
        # Find expired resources
        now = datetime.utcnow()

        result = await db.execute(
            select(ResourceListing).where(
                ResourceListing.cache_expires_at <= now
            )
        )

        expired_resources = result.scalars().all()

        print(f"Found {len(expired_resources)} expired resource cache entries")

        # For each expired resource, could fetch fresh data from 211 API
        # For now, we'll just extend the expiry or delete old entries

        for resource in expired_resources:
            # Simple approach: Delete very old entries (>30 days old)
            if resource.cached_at and (now - resource.cached_at).days > 30:
                await db.delete(resource)
                print(f"Deleted old resource: {resource.name}")

        await db.commit()

        print(f"Cache refresh complete")
