from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.shift import Shift, ShiftSignup, Organization
from app.schemas.shift import (
    ShiftCreate, ShiftUpdate, ShiftResponse, ShiftWithOrganization,
    ShiftSignupCreate, ShiftSignupUpdate, ShiftSignupResponse, ShiftSignupWithDetails,
    ShiftStatus
)
from app.api.auth import get_current_user
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    shift_data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new shift (authenticated users only)"""

    # Verify organization exists
    result = await db.execute(
        select(Organization).where(Organization.id == shift_data.organization_id)
    )
    organization = result.scalar_one_or_none()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Create shift
    shift_dict = shift_data.model_dump(exclude={'location_point'})
    shift_dict['coordinator_id'] = current_user.id

    # Handle location if provided
    if shift_data.location_point:
        lat = shift_data.location_point['lat']
        lon = shift_data.location_point['lon']
        shift_dict['location_point'] = from_shape(Point(lon, lat), srid=4326)

    shift = Shift(**shift_dict)
    db.add(shift)
    await db.commit()
    await db.refresh(shift)

    return shift


@router.get("", response_model=List[ShiftWithOrganization])
async def list_shifts(
    organization_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status_filter: Optional[ShiftStatus] = Query(None, alias="status"),
    available_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List shifts with filters"""

    query = select(Shift).options(selectinload(Shift.organization))

    # Apply filters
    filters = []

    if organization_id:
        filters.append(Shift.organization_id == organization_id)

    if start_date:
        filters.append(Shift.start_time >= start_date)

    if end_date:
        filters.append(Shift.end_time <= end_date)

    if status_filter:
        filters.append(Shift.status == status_filter)

    if available_only:
        filters.append(Shift.filled_count < Shift.capacity)
        filters.append(Shift.status == 'open')

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Shift.start_time).offset(skip).limit(limit)

    result = await db.execute(query)
    shifts = result.scalars().all()

    return shifts


@router.get("/{shift_id}", response_model=ShiftWithOrganization)
async def get_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get shift by ID"""
    result = await db.execute(
        select(Shift)
        .options(selectinload(Shift.organization))
        .where(Shift.id == shift_id)
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    return shift


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    shift_data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a shift (must be coordinator)"""
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id)
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    # Verify user is coordinator
    if shift.coordinator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the coordinator can update this shift"
        )

    # Update fields
    update_data = shift_data.model_dump(exclude_unset=True, exclude={'location_point'})
    for field, value in update_data.items():
        setattr(shift, field, value)

    # Handle location update
    if shift_data.location_point:
        lat = shift_data.location_point['lat']
        lon = shift_data.location_point['lon']
        shift.location_point = from_shape(Point(lon, lat), srid=4326)

    await db.commit()
    await db.refresh(shift)

    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a shift (must be coordinator)"""
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id)
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    # Verify user is coordinator
    if shift.coordinator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the coordinator can delete this shift"
        )

    await db.delete(shift)
    await db.commit()

    return None


# Shift Signup Endpoints

@router.post("/{shift_id}/signup", response_model=ShiftSignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_for_shift(
    shift_id: UUID,
    signup_data: ShiftSignupBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sign up for a shift"""

    # Get shift
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id)
    )
    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    # Check if shift is open and has capacity
    if shift.status != 'open':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift is not open for signups"
        )

    if shift.filled_count >= shift.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shift is full"
        )

    # Check if user already signed up
    existing_result = await db.execute(
        select(ShiftSignup).where(
            and_(
                ShiftSignup.shift_id == shift_id,
                ShiftSignup.volunteer_id == current_user.id,
                ShiftSignup.status == 'confirmed'
            )
        )
    )
    existing_signup = existing_result.scalar_one_or_none()

    if existing_signup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already signed up for this shift"
        )

    # Create signup
    signup = ShiftSignup(
        shift_id=shift_id,
        volunteer_id=current_user.id,
        notes=signup_data.notes
    )
    db.add(signup)

    # Update shift filled count
    shift.filled_count += 1
    if shift.filled_count >= shift.capacity:
        shift.status = 'full'

    await db.commit()
    await db.refresh(signup)

    return signup


@router.get("/my-shifts", response_model=List[ShiftSignupWithDetails])
async def get_my_shifts(
    status_filter: Optional[str] = Query(None, alias="status"),
    upcoming_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's shift signups"""

    query = select(ShiftSignup).options(
        selectinload(ShiftSignup.shift).selectinload(Shift.organization)
    ).where(ShiftSignup.volunteer_id == current_user.id)

    # Apply filters
    filters = []

    if status_filter:
        filters.append(ShiftSignup.status == status_filter)

    if upcoming_only:
        filters.append(Shift.start_time >= datetime.utcnow())

    if filters:
        query = query.join(Shift).where(and_(*filters))

    query = query.order_by(Shift.start_time.desc())

    result = await db.execute(query)
    signups = result.scalars().all()

    return signups


@router.put("/signups/{signup_id}", response_model=ShiftSignupResponse)
async def update_signup(
    signup_id: UUID,
    signup_data: ShiftSignupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a shift signup (cancel, etc.)"""
    result = await db.execute(
        select(ShiftSignup)
        .options(selectinload(ShiftSignup.shift))
        .where(ShiftSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signup not found"
        )

    # Verify user owns this signup
    if signup.volunteer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own signups"
        )

    # Update fields
    update_data = signup_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(signup, field, value)

    # If cancelling, update shift filled count
    if signup_data.status == 'cancelled' and signup.status == 'confirmed':
        signup.cancelled_at = datetime.utcnow()
        shift = signup.shift
        shift.filled_count = max(0, shift.filled_count - 1)
        if shift.status == 'full' and shift.filled_count < shift.capacity:
            shift.status = 'open'

    await db.commit()
    await db.refresh(signup)

    return signup


@router.delete("/signups/{signup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_signup(
    signup_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a shift signup"""
    result = await db.execute(
        select(ShiftSignup)
        .options(selectinload(ShiftSignup.shift))
        .where(ShiftSignup.id == signup_id)
    )
    signup = result.scalar_one_or_none()

    if not signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signup not found"
        )

    # Verify user owns this signup
    if signup.volunteer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own signups"
        )

    # Update signup status and shift count
    if signup.status == 'confirmed':
        signup.status = 'cancelled'
        signup.cancelled_at = datetime.utcnow()

        shift = signup.shift
        shift.filled_count = max(0, shift.filled_count - 1)
        if shift.status == 'full' and shift.filled_count < shift.capacity:
            shift.status = 'open'

    await db.commit()

    return None


# Import ShiftSignupBase at the top
from app.schemas.shift import ShiftSignupBase
