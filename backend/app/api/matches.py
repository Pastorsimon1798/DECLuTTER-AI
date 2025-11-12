"""Matches API endpoints for connecting needs with offers"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.post import Post, Match
from app.schemas.post import (
    MatchCreate,
    MatchUpdate,
    MatchResponse,
    MatchStatus,
)
from app.api.auth import get_current_user

router = APIRouter()


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a match (respond to a post)

    - **post_id**: ID of the post to respond to
    - **method**: Preferred contact method (in_app, sms, phone)
    - **notes**: Optional message to the post author
    """
    # Get the post
    result = await db.execute(select(Post).where(Post.id == match_data.post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check if post is still open
    if post.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post is {post.status}, cannot create match"
        )

    # Check if user is trying to match their own post
    if post.author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot match your own post"
        )

    # Check if match already exists
    existing_match = await db.execute(
        select(Match).where(
            and_(
                Match.post_id == match_data.post_id,
                Match.responder_id == current_user.id
            )
        )
    )
    if existing_match.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already responded to this post"
        )

    # Create match
    new_match = Match(
        post_id=post.id,
        responder_id=current_user.id,
        requester_id=post.author_id,
        method=match_data.method,
        notes=match_data.notes,
        status=MatchStatus.PENDING.value
    )

    db.add(new_match)

    # Update post status to 'matched'
    post.status = "matched"

    await db.commit()
    await db.refresh(new_match)

    # Get user details for response
    requester = await db.get(User, post.author_id)

    return MatchResponse(
        **{
            **new_match.__dict__,
            "post_title": post.title,
            "responder_pseudonym": current_user.pseudonym,
            "requester_pseudonym": requester.pseudonym
        }
    )


@router.get("", response_model=List[MatchResponse])
async def get_my_matches(
    as_requester: bool = Query(True, description="Get matches where you're the requester"),
    as_responder: bool = Query(True, description="Get matches where you're the responder"),
    status: Optional[MatchStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's matches

    Can filter by role (requester/responder) and status
    """
    # Build filters
    role_filters = []
    if as_requester:
        role_filters.append(Match.requester_id == current_user.id)
    if as_responder:
        role_filters.append(Match.responder_id == current_user.id)

    if not role_filters:
        return []

    filters = [or_(*role_filters)]

    if status:
        filters.append(Match.status == status.value)

    # Query matches with related post and users
    query = (
        select(Match, Post, User, User)
        .join(Post, Match.post_id == Post.id)
        .join(User, Match.responder_id == User.id)  # Responder
        .join(User, Match.requester_id == User.id, isouter=True)  # Requester
        .where(and_(*filters))
        .order_by(Match.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    rows = result.all()

    # Build response
    matches_response = []
    for match, post, responder, requester in rows:
        # Get actual responder and requester
        actual_responder = await db.get(User, match.responder_id)
        actual_requester = await db.get(User, match.requester_id)

        match_response = MatchResponse(
            **{
                **match.__dict__,
                "post_title": post.title,
                "responder_pseudonym": actual_responder.pseudonym,
                "requester_pseudonym": actual_requester.pseudonym
            }
        )
        matches_response.append(match_response)

    return matches_response


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific match by ID
    """
    result = await db.execute(
        select(Match, Post)
        .join(Post, Match.post_id == Post.id)
        .where(Match.id == match_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    match, post = row

    # Check if user is involved in this match
    if match.responder_id != current_user.id and match.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this match"
        )

    # Get user details
    responder = await db.get(User, match.responder_id)
    requester = await db.get(User, match.requester_id)

    return MatchResponse(
        **{
            **match.__dict__,
            "post_title": post.title,
            "responder_pseudonym": responder.pseudonym,
            "requester_pseudonym": requester.pseudonym
        }
    )


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: str,
    match_data: MatchUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update match status

    Only the requester (post author) can accept/decline
    Both parties can mark as completed
    """
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Check authorization based on action
    if match_data.status in [MatchStatus.ACCEPTED, MatchStatus.DECLINED]:
        # Only requester can accept/decline
        if match.requester_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the requester can accept or decline matches"
            )
    elif match_data.status == MatchStatus.COMPLETED:
        # Both parties can mark as completed
        if match.requester_id != current_user.id and match.responder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this match"
            )
    elif match_data.status == MatchStatus.CANCELLED:
        # Both parties can cancel
        if match.requester_id != current_user.id and match.responder_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this match"
            )

    # Update match
    match.status = match_data.status.value
    if match_data.notes:
        match.notes = match_data.notes

    if match_data.status == MatchStatus.COMPLETED:
        from datetime import datetime
        match.completed_at = datetime.utcnow()

        # Update post status to completed
        post = await db.get(Post, match.post_id)
        if post:
            post.status = "completed"

    await db.commit()
    await db.refresh(match)

    # Get details for response
    post = await db.get(Post, match.post_id)
    responder = await db.get(User, match.responder_id)
    requester = await db.get(User, match.requester_id)

    return MatchResponse(
        **{
            **match.__dict__,
            "post_title": post.title,
            "responder_pseudonym": responder.pseudonym,
            "requester_pseudonym": requester.pseudonym
        }
    )


@router.get("/post/{post_id}", response_model=List[MatchResponse])
async def get_post_matches(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all matches for a specific post

    Only post author can view all matches
    """
    # Get the post
    post = await db.get(Post, post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the post author can view all matches"
        )

    # Get all matches for this post
    result = await db.execute(
        select(Match)
        .where(Match.post_id == post_id)
        .order_by(Match.created_at.desc())
    )
    matches = result.scalars().all()

    # Build response
    matches_response = []
    for match in matches:
        responder = await db.get(User, match.responder_id)
        requester = await db.get(User, match.requester_id)

        match_response = MatchResponse(
            **{
                **match.__dict__,
                "post_title": post.title,
                "responder_pseudonym": responder.pseudonym,
                "requester_pseudonym": requester.pseudonym
            }
        )
        matches_response.append(match_response)

    return matches_response
