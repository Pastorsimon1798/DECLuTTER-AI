"""Tasks for expiring old posts and cleaning up data"""
from celery import shared_task
from datetime import datetime
from sqlalchemy import select, and_

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.post import Post


@celery_app.task(name="app.tasks.expiry.expire_old_posts")
def expire_old_posts():
    """Expire old posts that have passed their expiry date"""
    import asyncio
    asyncio.run(expire_old_posts_async())


async def expire_old_posts_async():
    """Async implementation of post expiry"""
    async with AsyncSessionLocal() as db:
        # Find posts that are expired and still open
        now = datetime.utcnow()

        result = await db.execute(
            select(Post).where(
                and_(
                    Post.expires_at <= now,
                    Post.status == 'open'
                )
            )
        )

        posts = result.scalars().all()

        for post in posts:
            post.status = 'cancelled'

        await db.commit()

        print(f"Expired {len(posts)} old posts")
