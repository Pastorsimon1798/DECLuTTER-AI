from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.shift import Organization
from app.schemas.shift import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.api.auth import get_current_user
from app.services.geohash_service import GeohashService
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organization (authenticated users only)"""

    # Check if slug already exists
    result = await db.execute(
        select(Organization).where(Organization.slug == organization_data.slug)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this slug already exists"
        )

    # Create organization
    org_dict = organization_data.model_dump(exclude={'location'})

    # Handle location if provided
    if organization_data.location:
        lat = organization_data.location['lat']
        lon = organization_data.location['lon']
        org_dict['location_geohash'] = GeohashService.encode_location(lat, lon, precision=7)
        org_dict['location_point'] = from_shape(Point(lon, lat), srid=4326)

    organization = Organization(**org_dict)
    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all organizations"""
    result = await db.execute(
        select(Organization)
        .order_by(Organization.name)
        .offset(skip)
        .limit(limit)
    )
    organizations = result.scalars().all()
    return organizations


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get organization by ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


@router.get("/slug/{slug}", response_model=OrganizationResponse)
async def get_organization_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get organization by slug"""
    result = await db.execute(
        select(Organization).where(Organization.slug == slug)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    organization_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an organization (authenticated users only)"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Update fields
    update_data = organization_data.model_dump(exclude_unset=True, exclude={'location'})
    for field, value in update_data.items():
        setattr(organization, field, value)

    # Handle location update
    if organization_data.location:
        lat = organization_data.location['lat']
        lon = organization_data.location['lon']
        organization.location_geohash = GeohashService.encode_location(lat, lon, precision=7)
        organization.location_point = from_shape(Point(lon, lat), srid=4326)

    await db.commit()
    await db.refresh(organization)

    return organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an organization (authenticated users only)"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    await db.delete(organization)
    await db.commit()

    return None
