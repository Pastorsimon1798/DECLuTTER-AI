from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.pod import Pod, PodMember, CheckIn, SOSBroadcast, PodPost
from app.schemas.pod import (
    PodCreate, PodUpdate, PodResponse,
    PodMemberCreate, PodMemberUpdate, PodMemberResponse,
    CheckInCreate, CheckInResponse,
    SOSBroadcastCreate, SOSBroadcastUpdate, SOSBroadcastResponse,
    PodPostCreate, PodPostUpdate, PodPostResponse,
    WellnessAlert
)
from app.api.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/pods", tags=["pods"])


# Helper function to check pod membership and role
async def check_pod_access(
    pod_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    required_role: Optional[str] = None
) -> PodMember:
    """Check if user has access to pod and optionally required role"""
    result = await db.execute(
        select(PodMember).where(
            and_(
                PodMember.pod_id == pod_id,
                PodMember.user_id == user_id,
                PodMember.status == 'active'
            )
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this pod"
        )

    if required_role and member.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You must be a {required_role} to perform this action"
        )

    return member


# Pod CRUD Operations

@router.post("", response_model=PodResponse, status_code=status.HTTP_201_CREATED)
async def create_pod(
    pod_data: PodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new pod and automatically make creator an admin"""
    # Create pod
    pod = Pod(
        **pod_data.model_dump(),
        created_by=current_user.id
    )
    db.add(pod)
    await db.flush()  # Get pod ID

    # Automatically add creator as admin
    creator_member = PodMember(
        pod_id=pod.id,
        user_id=current_user.id,
        role='admin',
        status='active'
    )
    db.add(creator_member)

    await db.commit()
    await db.refresh(pod)

    # Return with member count and role
    response = PodResponse.model_validate(pod)
    response.member_count = 1
    response.my_role = 'admin'

    return response


@router.get("", response_model=List[PodResponse])
async def list_my_pods(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List all pods the current user is a member of"""
    # Return empty if no user (for testing without auth)
    if not current_user:
        return []
    # Get user's pod memberships
    result = await db.execute(
        select(PodMember).where(
            and_(
                PodMember.user_id == current_user.id,
                PodMember.status.in_(['active', 'pending'])
            )
        )
        .options(selectinload(PodMember.pod))
        .offset(skip)
        .limit(limit)
    )
    memberships = result.scalars().all()

    # Build response with member counts and roles
    responses = []
    for membership in memberships:
        pod = membership.pod
        if pod:
            # Count active members
            member_count_result = await db.execute(
                select(func.count(PodMember.id)).where(
                    and_(
                        PodMember.pod_id == pod.id,
                        PodMember.status == 'active'
                    )
                )
            )
            member_count = member_count_result.scalar()

            response = PodResponse.model_validate(pod)
            response.member_count = member_count or 0
            response.my_role = membership.role
            responses.append(response)

    return responses


@router.get("/{pod_id}", response_model=PodResponse)
async def get_pod(
    pod_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pod details"""
    # Check access
    membership = await check_pod_access(pod_id, current_user.id, db)

    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pod not found"
        )

    # Count members
    member_count_result = await db.execute(
        select(func.count(PodMember.id)).where(
            and_(
                PodMember.pod_id == pod_id,
                PodMember.status == 'active'
            )
        )
    )
    member_count = member_count_result.scalar()

    response = PodResponse.model_validate(pod)
    response.member_count = member_count or 0
    response.my_role = membership.role

    return response


@router.put("/{pod_id}", response_model=PodResponse)
async def update_pod(
    pod_id: UUID,
    pod_data: PodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update pod settings (admin only)"""
    # Check admin access
    await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pod not found"
        )

    # Update fields
    update_data = pod_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pod, field, value)

    await db.commit()
    await db.refresh(pod)

    return pod


@router.delete("/{pod_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pod(
    pod_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a pod (admin only)"""
    # Check admin access
    await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pod not found"
        )

    await db.delete(pod)
    await db.commit()

    return None


# Pod Member Management

@router.post("/{pod_id}/members", response_model=PodMemberResponse, status_code=status.HTTP_201_CREATED)
async def join_pod(
    pod_id: UUID,
    member_data: PodMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join a pod or invite a member (if admin)"""
    # Get pod
    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pod not found"
        )

    # Determine user to add
    user_to_add = member_data.user_id if member_data.user_id else current_user.id

    # If inviting someone else, must be admin
    if user_to_add != current_user.id:
        await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    # Check if already a member
    existing_result = await db.execute(
        select(PodMember).where(
            and_(
                PodMember.pod_id == pod_id,
                PodMember.user_id == user_to_add
            )
        )
    )
    existing_member = existing_result.scalar_one_or_none()

    if existing_member:
        if existing_member.status == 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already a member of this pod"
            )
        else:
            # Reactivate membership
            existing_member.status = 'active' if not pod.is_private else 'pending'
            await db.commit()
            await db.refresh(existing_member)
            return existing_member

    # Check capacity
    member_count_result = await db.execute(
        select(func.count(PodMember.id)).where(
            and_(
                PodMember.pod_id == pod_id,
                PodMember.status == 'active'
            )
        )
    )
    member_count = member_count_result.scalar()

    if member_count >= pod.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pod is at maximum capacity"
        )

    # Create membership
    new_member = PodMember(
        pod_id=pod_id,
        user_id=user_to_add,
        status='active' if not pod.is_private else 'pending'
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return new_member


@router.get("/{pod_id}/members", response_model=List[PodMemberResponse])
async def list_pod_members(
    pod_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all members of a pod"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    result = await db.execute(
        select(PodMember)
        .where(PodMember.pod_id == pod_id)
        .options(selectinload(PodMember.user))
        .order_by(desc(PodMember.joined_at))
    )
    members = result.scalars().all()

    # Add user info
    responses = []
    for member in members:
        response = PodMemberResponse.model_validate(member)
        if member.user:
            response.user_name = member.user.pseudonym
            response.user_email = member.user.email
        responses.append(response)

    return responses


@router.put("/{pod_id}/members/{member_id}", response_model=PodMemberResponse)
async def update_pod_member(
    pod_id: UUID,
    member_id: UUID,
    member_data: PodMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member role or status (admin only)"""
    # Check admin access
    await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    result = await db.execute(
        select(PodMember).where(PodMember.id == member_id)
    )
    member = result.scalar_one_or_none()

    if not member or member.pod_id != pod_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Update fields
    update_data = member_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    await db.commit()
    await db.refresh(member)

    return member


@router.delete("/{pod_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_pod_member(
    pod_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from pod (admin only or self)"""
    result = await db.execute(
        select(PodMember).where(PodMember.id == member_id)
    )
    member = result.scalar_one_or_none()

    if not member or member.pod_id != pod_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Can remove self or must be admin
    if member.user_id != current_user.id:
        await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    member.status = 'inactive'
    await db.commit()

    return None


# Check-In Endpoints

@router.post("/{pod_id}/check-ins", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_check_in(
    pod_id: UUID,
    check_in_data: CheckInCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a wellness check-in"""
    # Check access and get membership
    membership = await check_pod_access(pod_id, current_user.id, db)

    # Create check-in
    check_in = CheckIn(
        pod_id=pod_id,
        member_id=membership.id,
        user_id=current_user.id,
        **check_in_data.model_dump()
    )
    db.add(check_in)

    # Update member's last check-in
    membership.last_check_in_at = datetime.utcnow()
    membership.consecutive_missed_checkins = 0

    await db.commit()
    await db.refresh(check_in)

    return check_in


@router.get("/{pod_id}/check-ins", response_model=List[CheckInResponse])
async def list_check_ins(
    pod_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List recent check-ins for the pod"""
    # Check access
    membership = await check_pod_access(pod_id, current_user.id, db)

    # Admins see all, members see non-private
    if membership.role == 'admin':
        query = select(CheckIn).where(CheckIn.pod_id == pod_id)
    else:
        query = select(CheckIn).where(
            and_(
                CheckIn.pod_id == pod_id,
                or_(
                    CheckIn.is_private == False,
                    CheckIn.user_id == current_user.id
                )
            )
        )

    result = await db.execute(
        query.options(selectinload(CheckIn.user))
        .order_by(desc(CheckIn.created_at))
        .limit(limit)
    )
    check_ins = result.scalars().all()

    # Add user names
    responses = []
    for check_in in check_ins:
        response = CheckInResponse.model_validate(check_in)
        if check_in.user:
            response.user_name = check_in.user.pseudonym
        responses.append(response)

    return responses


@router.get("/{pod_id}/wellness", response_model=List[WellnessAlert])
async def get_wellness_alerts(
    pod_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get wellness alerts for members who haven't checked in (admin only)"""
    # Check admin access
    await check_pod_access(pod_id, current_user.id, db, required_role='admin')

    # Get pod to check settings
    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod or not pod.enable_wellness_alerts:
        return []

    # Find members who haven't checked in recently
    threshold_date = datetime.utcnow() - timedelta(days=pod.check_in_frequency_days)

    result = await db.execute(
        select(PodMember)
        .where(
            and_(
                PodMember.pod_id == pod_id,
                PodMember.status == 'active',
                or_(
                    PodMember.last_check_in_at == None,
                    PodMember.last_check_in_at < threshold_date
                ),
                PodMember.consecutive_missed_checkins >= pod.missed_checkins_threshold
            )
        )
        .options(selectinload(PodMember.user))
    )
    at_risk_members = result.scalars().all()

    # Build wellness alerts
    alerts = []
    for member in at_risk_members:
        days_since = None
        if member.last_check_in_at:
            days_since = (datetime.utcnow() - member.last_check_in_at).days

        alerts.append(WellnessAlert(
            member_id=member.id,
            user_id=member.user_id,
            user_name=member.user.pseudonym if member.user else "Unknown",
            last_check_in_at=member.last_check_in_at,
            consecutive_missed_checkins=member.consecutive_missed_checkins,
            days_since_last_checkin=days_since
        ))

    return alerts


# SOS Broadcast Endpoints

@router.post("/{pod_id}/sos", response_model=SOSBroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_sos_broadcast(
    pod_id: UUID,
    sos_data: SOSBroadcastCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send an SOS broadcast to all pod members"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    # Get pod to check if SOS is enabled
    result = await db.execute(
        select(Pod).where(Pod.id == pod_id)
    )
    pod = result.scalar_one_or_none()

    if not pod or not pod.enable_sos_broadcasts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SOS broadcasts are not enabled for this pod"
        )

    # Create SOS broadcast
    sos = SOSBroadcast(
        pod_id=pod_id,
        user_id=current_user.id,
        **sos_data.model_dump()
    )
    db.add(sos)
    await db.commit()
    await db.refresh(sos)

    # TODO: Trigger Celery task to notify all pod members
    # send_sos_notifications.delay(sos.id)

    return sos


@router.get("/{pod_id}/sos", response_model=List[SOSBroadcastResponse])
async def list_sos_broadcasts(
    pod_id: UUID,
    include_resolved: bool = False,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List SOS broadcasts for the pod"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    filters = [SOSBroadcast.pod_id == pod_id]
    if not include_resolved:
        filters.append(SOSBroadcast.is_resolved == False)

    result = await db.execute(
        select(SOSBroadcast)
        .where(and_(*filters))
        .options(selectinload(SOSBroadcast.user))
        .order_by(desc(SOSBroadcast.created_at))
        .limit(limit)
    )
    broadcasts = result.scalars().all()

    # Add user names
    responses = []
    for broadcast in broadcasts:
        response = SOSBroadcastResponse.model_validate(broadcast)
        if broadcast.user:
            response.user_name = broadcast.user.pseudonym
        responses.append(response)

    return responses


@router.put("/{pod_id}/sos/{sos_id}", response_model=SOSBroadcastResponse)
async def update_sos_broadcast(
    pod_id: UUID,
    sos_id: UUID,
    sos_data: SOSBroadcastUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark an SOS broadcast as resolved"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    result = await db.execute(
        select(SOSBroadcast).where(SOSBroadcast.id == sos_id)
    )
    sos = result.scalar_one_or_none()

    if not sos or sos.pod_id != pod_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS broadcast not found"
        )

    if sos_data.is_resolved:
        sos.is_resolved = True
        sos.resolved_at = datetime.utcnow()
        sos.resolved_by = current_user.id

    await db.commit()
    await db.refresh(sos)

    return sos


# Pod Posts Endpoints

@router.post("/{pod_id}/posts", response_model=PodPostResponse, status_code=status.HTTP_201_CREATED)
async def create_pod_post(
    pod_id: UUID,
    post_data: PodPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a post within the pod"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    post = PodPost(
        pod_id=pod_id,
        user_id=current_user.id,
        **post_data.model_dump()
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post


@router.get("/{pod_id}/posts", response_model=List[PodPostResponse])
async def list_pod_posts(
    pod_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List posts in the pod (pinned first)"""
    # Check access
    await check_pod_access(pod_id, current_user.id, db)

    result = await db.execute(
        select(PodPost)
        .where(PodPost.pod_id == pod_id)
        .options(selectinload(PodPost.user))
        .order_by(desc(PodPost.is_pinned), desc(PodPost.created_at))
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()

    # Add user names
    responses = []
    for post in posts:
        response = PodPostResponse.model_validate(post)
        if post.user:
            response.user_name = post.user.pseudonym
        responses.append(response)

    return responses


@router.put("/{pod_id}/posts/{post_id}", response_model=PodPostResponse)
async def update_pod_post(
    pod_id: UUID,
    post_id: UUID,
    post_data: PodPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a pod post (author or admin)"""
    result = await db.execute(
        select(PodPost).where(PodPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post or post.pod_id != pod_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Get membership to check role
    membership = await check_pod_access(pod_id, current_user.id, db)

    # Can edit own posts or if admin
    if post.user_id != current_user.id and membership.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts"
        )

    # Update fields
    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'is_pinned' and membership.role != 'admin':
            continue  # Only admins can pin
        setattr(post, field, value)

    if post_data.is_pinned is not None and membership.role == 'admin':
        post.is_pinned = post_data.is_pinned
        if post_data.is_pinned:
            post.pinned_by = current_user.id

    await db.commit()
    await db.refresh(post)

    return post


@router.delete("/{pod_id}/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pod_post(
    pod_id: UUID,
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a pod post (author or admin)"""
    result = await db.execute(
        select(PodPost).where(PodPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post or post.pod_id != pod_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Get membership to check role
    membership = await check_pod_access(pod_id, current_user.id, db)

    # Can delete own posts or if admin
    if post.user_id != current_user.id and membership.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )

    await db.delete(post)
    await db.commit()

    return None
