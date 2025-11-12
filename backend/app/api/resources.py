from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.resource import ResourceListing, ResourceBookmark
from app.schemas.resource import (
    ResourceListingCreate, ResourceListingUpdate, ResourceListingResponse,
    ResourceBookmarkCreate, ResourceBookmarkUpdate, ResourceBookmarkResponse,
    ResourceBookmarkWithDetails, ResourceSearchParams
)
from app.api.auth import get_current_user
from app.services.geohash_service import GeohashService
from app.services.two11_client import two11_client
from geoalchemy2.shape import from_shape
from geoalchemy2.functions import ST_DWithin, ST_Distance
from shapely.geometry import Point
from geoalchemy2 import WKTElement


router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/search", response_model=List[ResourceListingResponse])
async def search_resources(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = Query(5000, ge=100, le=50000),  # meters
    category: Optional[str] = None,
    query: Optional[str] = None,
    open_now: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Search for resources with location and filters

    This endpoint searches cached resources first, then falls back to 211 API
    if cache is empty or expired.
    """

    filters = []

    # Category filter
    if category:
        filters.append(ResourceListing.category == category)

    # Text search in name and description
    if query:
        search_filter = or_(
            ResourceListing.name.ilike(f"%{query}%"),
            ResourceListing.description.ilike(f"%{query}%")
        )
        filters.append(search_filter)

    # Base query
    query_obj = select(ResourceListing)

    # Location-based search
    if lat and lon:
        # Create point for search location
        search_point = WKTElement(f'POINT({lon} {lat})', srid=4326)

        # Filter by distance
        filters.append(
            ST_DWithin(
                ResourceListing.location_point,
                search_point,
                radius
            )
        )

        # Order by distance
        query_obj = query_obj.order_by(
            ST_Distance(ResourceListing.location_point, search_point)
        )
    else:
        # Order by name if no location
        query_obj = query_obj.order_by(ResourceListing.name)

    # Apply all filters
    if filters:
        query_obj = query_obj.where(and_(*filters))

    # Apply pagination
    query_obj = query_obj.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query_obj)
    resources = result.scalars().all()

    # If no cached resources and we have location, try 211 API
    if len(resources) == 0 and lat and lon:
        try:
            # Fetch from 211 API
            api_results = await two11_client.search_organizations(
                lat=lat,
                lon=lon,
                radius=radius,
                category=category,
                query=query,
                limit=limit
            )

            # Cache the results
            for org_data in api_results:
                resource_data = two11_client.parse_organization_to_resource(org_data)

                # Create resource listing
                resource_dict = resource_data.copy()
                location = resource_dict.pop('location', None)

                # Add cache expiry (7 days)
                resource_dict['cache_expires_at'] = datetime.utcnow() + timedelta(days=7)

                # Handle location
                if location:
                    resource_dict['location_geohash'] = GeohashService.encode_location(
                        location['lat'], location['lon'], precision=7
                    )
                    resource_dict['location_point'] = from_shape(
                        Point(location['lon'], location['lat']), srid=4326
                    )

                resource = ResourceListing(**resource_dict)
                db.add(resource)
                resources.append(resource)

            await db.commit()

        except Exception as e:
            print(f"Error fetching from 211 API: {e}")

    # Check bookmarks for current user
    if current_user:
        resource_ids = [r.id for r in resources]
        bookmark_result = await db.execute(
            select(ResourceBookmark).where(
                and_(
                    ResourceBookmark.user_id == current_user.id,
                    ResourceBookmark.resource_id.in_(resource_ids)
                )
            )
        )
        bookmarks = bookmark_result.scalars().all()
        bookmark_map = {b.resource_id: b.id for b in bookmarks}

        # Add bookmark info to response
        response_resources = []
        for resource in resources:
            resource_dict = ResourceListingResponse.from_orm(resource).dict()
            resource_dict['is_bookmarked'] = resource.id in bookmark_map
            resource_dict['bookmark_id'] = bookmark_map.get(resource.id)
            response_resources.append(ResourceListingResponse(**resource_dict))

        return response_resources

    return resources


@router.get("/{resource_id}", response_model=ResourceListingResponse)
async def get_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get resource by ID"""
    result = await db.execute(
        select(ResourceListing).where(ResourceListing.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    # Check if user has bookmarked this resource
    resource_dict = ResourceListingResponse.from_orm(resource).dict()
    if current_user:
        bookmark_result = await db.execute(
            select(ResourceBookmark).where(
                and_(
                    ResourceBookmark.user_id == current_user.id,
                    ResourceBookmark.resource_id == resource_id
                )
            )
        )
        bookmark = bookmark_result.scalar_one_or_none()
        resource_dict['is_bookmarked'] = bookmark is not None
        resource_dict['bookmark_id'] = bookmark.id if bookmark else None

    return ResourceListingResponse(**resource_dict)


@router.post("", response_model=ResourceListingResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new resource (admin/community members can add local resources)"""

    # Create resource
    resource_dict = resource_data.model_dump(exclude={'location'})

    # Set cache expiry (7 days default)
    resource_dict['cache_expires_at'] = datetime.utcnow() + timedelta(days=7)

    # Handle location if provided
    if resource_data.location:
        lat = resource_data.location['lat']
        lon = resource_data.location['lon']
        resource_dict['location_geohash'] = GeohashService.encode_location(lat, lon, precision=7)
        resource_dict['location_point'] = from_shape(Point(lon, lat), srid=4326)

    resource = ResourceListing(**resource_dict)
    db.add(resource)
    await db.commit()
    await db.refresh(resource)

    return resource


@router.put("/{resource_id}", response_model=ResourceListingResponse)
async def update_resource(
    resource_id: UUID,
    resource_data: ResourceListingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a resource"""
    result = await db.execute(
        select(ResourceListing).where(ResourceListing.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    # Update fields
    update_data = resource_data.model_dump(exclude_unset=True, exclude={'location'})
    for field, value in update_data.items():
        setattr(resource, field, value)

    # Handle location update
    if resource_data.location:
        lat = resource_data.location['lat']
        lon = resource_data.location['lon']
        resource.location_geohash = GeohashService.encode_location(lat, lon, precision=7)
        resource.location_point = from_shape(Point(lon, lat), srid=4326)

    await db.commit()
    await db.refresh(resource)

    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a resource"""
    result = await db.execute(
        select(ResourceListing).where(ResourceListing.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    await db.delete(resource)
    await db.commit()

    return None


# Bookmark Endpoints

@router.post("/bookmarks", response_model=ResourceBookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: ResourceBookmarkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bookmark a resource"""

    # Check if resource exists
    result = await db.execute(
        select(ResourceListing).where(ResourceListing.id == bookmark_data.resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    # Check if already bookmarked
    existing_result = await db.execute(
        select(ResourceBookmark).where(
            and_(
                ResourceBookmark.user_id == current_user.id,
                ResourceBookmark.resource_id == bookmark_data.resource_id
            )
        )
    )
    existing_bookmark = existing_result.scalar_one_or_none()

    if existing_bookmark:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resource already bookmarked"
        )

    # Create bookmark
    bookmark = ResourceBookmark(
        user_id=current_user.id,
        resource_id=bookmark_data.resource_id,
        notes=bookmark_data.notes
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return bookmark


@router.get("/bookmarks/my", response_model=List[ResourceBookmarkWithDetails])
async def get_my_bookmarks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's bookmarked resources"""
    result = await db.execute(
        select(ResourceBookmark)
        .options(selectinload(ResourceBookmark.resource))
        .where(ResourceBookmark.user_id == current_user.id)
        .order_by(ResourceBookmark.created_at.desc())
    )
    bookmarks = result.scalars().all()

    return bookmarks


@router.put("/bookmarks/{bookmark_id}", response_model=ResourceBookmarkResponse)
async def update_bookmark(
    bookmark_id: UUID,
    bookmark_data: ResourceBookmarkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a bookmark"""
    result = await db.execute(
        select(ResourceBookmark).where(ResourceBookmark.id == bookmark_id)
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    # Verify user owns this bookmark
    if bookmark.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own bookmarks"
        )

    # Update fields
    update_data = bookmark_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bookmark, field, value)

    await db.commit()
    await db.refresh(bookmark)

    return bookmark


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a bookmark"""
    result = await db.execute(
        select(ResourceBookmark).where(ResourceBookmark.id == bookmark_id)
    )
    bookmark = result.scalar_one_or_none()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    # Verify user owns this bookmark
    if bookmark.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own bookmarks"
        )

    await db.delete(bookmark)
    await db.commit()

    return None
