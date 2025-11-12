from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, asc, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum

from app.database import get_db
from app.models.user import User
from app.models.resource import ResourceListing, ResourceBookmark
from app.schemas.resource import (
    ResourceListingCreate, ResourceListingUpdate, ResourceListingResponse,
    ResourceBookmarkCreate, ResourceBookmarkUpdate, ResourceBookmarkResponse,
    ResourceBookmarkWithDetails, ResourceSearchParams, ResourceVerificationCreate
)
from app.api.auth import get_current_user, get_current_user_optional
from app.services.geohash_service import GeohashService
from app.services.two11_client import two11_client
from geoalchemy2.shape import from_shape, to_shape
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_X, ST_Y
from shapely.geometry import Point
from geoalchemy2 import WKTElement


router = APIRouter(prefix="/resources", tags=["resources"])


class ResourceSortBy(str, Enum):
    """Sorting options for resources"""
    DISTANCE = "distance"  # Closest first (requires lat/lon)
    NAME_ASC = "name_asc"  # Name A-Z
    NAME_DESC = "name_desc"  # Name Z-A
    RECENT = "recent"  # Most recently added
    VERIFIED = "verified"  # Most verified first
    CATEGORY = "category"  # By category then name


@router.get("/search", response_model=List[ResourceListingResponse])
async def search_resources(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = Query(5000, ge=100, le=804672),  # meters (up to 500 miles)
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    query: Optional[str] = None,
    open_now: bool = False,
    population_tags: Optional[str] = None,  # Comma-separated list
    is_community_contributed: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=2000),  # Increased max to 2000 for large radius searches
    sort_by: ResourceSortBy = Query(ResourceSortBy.DISTANCE, description="Sort order for results"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search for resources with location and filters

    This endpoint searches cached resources first, then falls back to 211 API
    if cache is empty or expired.

    Phase 3.5: Supports expanded categories and population-specific filters
    """

    filters = []

    # Category filter
    if category:
        filters.append(ResourceListing.category == category)

    # Subcategory filter (Phase 3.5)
    if subcategory:
        filters.append(ResourceListing.subcategory == subcategory)

    # Text search in name and description
    if query:
        search_filter = or_(
            ResourceListing.name.ilike(f"%{query}%"),
            ResourceListing.description.ilike(f"%{query}%")
        )
        filters.append(search_filter)

    # Population tags filter (Phase 3.5)
    if population_tags:
        tags_list = [tag.strip() for tag in population_tags.split(',')]
        # Use overlap operator to check if any tag matches
        filters.append(ResourceListing.population_tags.overlap(tags_list))

    # Community contributed filter (Phase 3.5)
    if is_community_contributed is not None:
        filters.append(ResourceListing.is_community_contributed == is_community_contributed)

    # Base query
    query_obj = select(ResourceListing)

    # Create search point if location provided (for distance calculations)
    search_point = None
    if lat and lon:
        search_point = WKTElement(f'POINT({lon} {lat})', srid=4326)
        # Filter by distance
        filters.append(
            ST_DWithin(
                ResourceListing.location_point,
                search_point,
                radius
            )
        )

    # Apply sorting based on sort_by parameter
    if sort_by == ResourceSortBy.DISTANCE:
        if search_point:
            # Order by distance (closest first)
            query_obj = query_obj.order_by(
                ST_Distance(ResourceListing.location_point, search_point)
            )
        else:
            # Fallback to name if no location
            query_obj = query_obj.order_by(ResourceListing.name)
    elif sort_by == ResourceSortBy.NAME_ASC:
        query_obj = query_obj.order_by(ResourceListing.name)
    elif sort_by == ResourceSortBy.NAME_DESC:
        query_obj = query_obj.order_by(desc(ResourceListing.name))
    elif sort_by == ResourceSortBy.RECENT:
        query_obj = query_obj.order_by(desc(ResourceListing.created_at))
    elif sort_by == ResourceSortBy.VERIFIED:
        # Most verified first, then by verification date, then by name
        query_obj = query_obj.order_by(
            desc(ResourceListing.verification_count),
            desc(ResourceListing.verified_at),
            ResourceListing.name
        )
    elif sort_by == ResourceSortBy.CATEGORY:
        # By category, then by name
        query_obj = query_obj.order_by(
            ResourceListing.category,
            ResourceListing.name
        )
    else:
        # Default: name ascending
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

    # Build response with coordinates and bookmark info
    response_resources = []
    bookmark_map = {}
    
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

    # Convert resources to response format with coordinates
    for resource in resources:
        resource_dict = ResourceListingResponse.model_validate(resource).model_dump()
        
        # Extract lat/lon from location_point for map display
        if resource.location_point:
            try:
                point = to_shape(resource.location_point)
                resource_dict['lat'] = point.y
                resource_dict['lon'] = point.x
            except Exception as e:
                print(f"Error extracting coordinates for resource {resource.id}: {e}")
        
        # Add bookmark info if user is logged in
        if current_user:
            resource_dict['is_bookmarked'] = resource.id in bookmark_map
            resource_dict['bookmark_id'] = bookmark_map.get(resource.id)
        
        response_resources.append(ResourceListingResponse(**resource_dict))

    return response_resources


@router.get("/{resource_id}", response_model=ResourceListingResponse)
async def get_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
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
    resource_dict = ResourceListingResponse.model_validate(resource).model_dump()
    
    # Extract lat/lon from location_point for map display
    if resource.location_point:
        try:
            point = to_shape(resource.location_point)
            resource_dict['lat'] = point.y
            resource_dict['lon'] = point.x
        except Exception as e:
            print(f"Error extracting coordinates for resource {resource.id}: {e}")
    
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
    """
    Create a new resource (community members can add local resources)

    Phase 3.5: Community-contributed resources are marked with is_community_contributed=True
    """

    # Create resource
    resource_dict = resource_data.model_dump(exclude={'location'})

    # Set cache expiry (7 days default)
    resource_dict['cache_expires_at'] = datetime.utcnow() + timedelta(days=7)

    # Mark as community-contributed (Phase 3.5)
    resource_dict['is_community_contributed'] = True

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


# Phase 3.5: Community Verification Endpoint

@router.post("/{resource_id}/verify", response_model=ResourceListingResponse)
async def verify_resource(
    resource_id: UUID,
    verification_data: ResourceVerificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Community verification for resources

    Users can verify that a resource's information is accurate.
    This helps build trust in community-contributed data.
    """
    result = await db.execute(
        select(ResourceListing).where(ResourceListing.id == resource_id)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    # Only increment if verification is positive
    if verification_data.is_accurate:
        resource.verification_count += 1
        resource.verified_by = current_user.id
        resource.verified_at = datetime.utcnow()
        resource.last_verified_at = datetime.utcnow()

    await db.commit()
    await db.refresh(resource)

    return resource
