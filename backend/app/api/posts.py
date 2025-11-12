"""Posts API endpoints for Needs & Offers Board (Project 1)"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.post import Post, Match
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostSearchParams,
    PostType,
    PostStatus,
    MatchCreate,
    MatchUpdate,
    MatchResponse,
)
from app.api.auth import get_current_user, get_current_user_optional
from app.services.geohash_service import GeohashService
from geoalchemy2.functions import ST_MakePoint, ST_Distance
from geoalchemy2 import Geography

router = APIRouter()


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new need or offer post

    - **type**: NEED or OFFER
    - **category**: Category (food, transport, housing, etc.)
    - **title**: Short title
    - **description**: Detailed description
    - **location**: Lat/lon coordinates
    - **radius_meters**: Search radius (100-804672 meters, up to 500 miles)
    - **visibility**: public, circles, or private
    """
    # Encode location to geohash for privacy
    geohash_str = GeohashService.encode_location(
        post_data.location.lat,
        post_data.location.lon
    )

    # Create post
    new_post = Post(
        type=post_data.type.value,
        category=post_data.category.lower(),
        title=post_data.title,
        description=post_data.description,
        location_geohash=geohash_str,
        # Store exact location for distance calculations (internal only)
        location_point=f"POINT({post_data.location.lon} {post_data.location.lat})",
        radius_meters=post_data.radius_meters,
        author_id=current_user.id,
        visibility=post_data.visibility.value,
        status=PostStatus.OPEN.value,
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    # Build response
    response = PostResponse(
        **{
            **new_post.__dict__,
            "author_pseudonym": current_user.pseudonym
        }
    )

    return response


@router.get("", response_model=List[PostResponse])
async def search_posts(
    type: Optional[PostType] = Query(None, description="Filter by type (NEED or OFFER)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="User latitude"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="User longitude"),
    radius: int = Query(5000, ge=100, le=804672, description="Search radius in meters (up to 500 miles)"),
    status: PostStatus = Query(PostStatus.OPEN, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search for posts with optional filters

    Returns posts within specified radius if location provided,
    otherwise returns recent posts matching other criteria.
    """
    # Build base query
    query = select(Post, User).join(User, Post.author_id == User.id)

    # Apply filters
    filters = [Post.status == status.value]

    if type:
        filters.append(Post.type == type.value)

    if category:
        filters.append(Post.category == category.lower())

    # Only show public posts or user's own posts
    if current_user:
        filters.append(
            or_(
                Post.visibility == "public",
                Post.author_id == current_user.id
            )
        )
    else:
        filters.append(Post.visibility == "public")

    query = query.where(and_(*filters))

    # Location-based search
    if lat is not None and lon is not None:
        user_geohash = GeohashService.encode_location(lat, lon)
        search_cells = GeohashService.get_search_cells(user_geohash, radius)

        # Filter by geohash cells
        geohash_filters = [Post.location_geohash.like(f"{cell}%") for cell in search_cells]
        query = query.where(or_(*geohash_filters))

    # Order by creation date (most recent first)
    query = query.order_by(Post.created_at.desc())

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    # Build response with calculated distances
    posts_response = []
    for post, author in rows:
        # Calculate distance if user location provided
        distance = None
        if lat is not None and lon is not None:
            post_lat, post_lon = GeohashService.decode_location(post.location_geohash)
            distance = int(GeohashService.calculate_distance(lat, lon, post_lat, post_lon))

            # Filter out posts beyond radius
            if distance > radius:
                continue

        post_response = PostResponse(
            **{
                **post.__dict__,
                "author_pseudonym": author.pseudonym,
                "distance_meters": distance
            }
        )
        posts_response.append(post_response)

    # Sort by distance if available
    if lat is not None and lon is not None:
        posts_response.sort(key=lambda p: p.distance_meters if p.distance_meters else float('inf'))

    return posts_response


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get a specific post by ID
    """
    result = await db.execute(
        select(Post, User)
        .join(User, Post.author_id == User.id)
        .where(Post.id == post_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    post, author = row

    # Check visibility
    if post.visibility != "public":
        if not current_user or (post.author_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this post"
            )

    return PostResponse(
        **{
            **post.__dict__,
            "author_pseudonym": author.pseudonym
        }
    )


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a post (only by author)
    """
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    # Update fields
    update_data = post_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(post, field):
            setattr(post, field, value)

    post.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(post)

    return PostResponse(
        **{
            **post.__dict__,
            "author_pseudonym": current_user.pseudonym
        }
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post (only by author)
    """
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )

    await db.delete(post)
    await db.commit()

    return None


@router.get("/my/posts", response_model=List[PostResponse])
async def get_my_posts(
    type: Optional[PostType] = None,
    status: Optional[PostStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's posts
    """
    # Return empty if no user (for testing without auth)
    if not current_user:
        return []
    
    filters = [Post.author_id == current_user.id]

    if type:
        filters.append(Post.type == type.value)

    if status:
        filters.append(Post.status == status.value)

    query = (
        select(Post)
        .where(and_(*filters))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    posts = result.scalars().all()

    return [
        PostResponse(
            **{
                **post.__dict__,
                "author_pseudonym": current_user.pseudonym
            }
        )
        for post in posts
    ]
