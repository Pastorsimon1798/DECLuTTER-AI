"""Authentication API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional
from datetime import timedelta

from app.database import get_db
from app.models.user import User, UserProfile
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    PhoneVerificationRequest,
    PhoneVerificationConfirm,
    TokenData,
)
from app.utils.security import (
    hash_password,
    verify_password,
    hash_phone_number,
    create_access_token,
    decode_access_token,
    generate_verification_code,
)
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# Temporary storage for verification codes (in production, use Redis)
verification_codes = {}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user

    - **pseudonym**: Unique display name (3-50 characters)
    - **email**: Optional email address
    - **phone**: Optional phone number (E.164 format recommended)
    - **password**: Password (min 8 characters, must include uppercase, lowercase, digit)
    - **locale**: Language preference (default: 'en')
    """
    # Check if pseudonym already exists
    result = await db.execute(select(User).where(User.pseudonym == user_data.pseudonym))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pseudonym already registered"
        )

    # Check if email already exists (if provided)
    if user_data.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Check if phone already exists (if provided)
    phone_hash = None
    if user_data.phone:
        phone_hash = hash_phone_number(user_data.phone)
        result = await db.execute(select(User).where(User.phone_hash == phone_hash))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )

    # Validate that either email or phone is provided
    if not user_data.email and not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone number must be provided"
        )

    # Validate that password is provided
    if not user_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        pseudonym=user_data.pseudonym,
        email=user_data.email,
        phone_hash=phone_hash,
        hashed_password=hashed_password,
        locale=user_data.locale,
        timezone=user_data.timezone,
    )

    db.add(new_user)
    await db.flush()

    # Create user profile
    profile = UserProfile(user_id=new_user.id)
    db.add(profile)

    await db.commit()
    await db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username (email, phone, or pseudonym) and password

    Returns JWT access token for authenticated requests
    """
    # Find user by email, pseudonym, or phone hash
    username = form_data.username
    phone_hash = hash_phone_number(username) if username.startswith('+') else None

    query = select(User).where(
        or_(
            User.email == username,
            User.pseudonym == username,
            User.phone_hash == phone_hash if phone_hash else False
        )
    )

    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # Verify user and password
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information
    """
    return UserResponse.from_orm(current_user)


@router.post("/verify-phone/request")
async def request_phone_verification(
    data: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Request phone verification code

    Sends a 6-digit code via SMS to the provided phone number
    """
    # Generate verification code
    code = generate_verification_code()

    # Store code temporarily (in production, use Redis with TTL)
    verification_codes[data.phone] = {
        "code": code,
        "user_id": str(current_user.id)
    }

    # TODO: Send SMS with code using Plivo
    # For now, return code in development (remove in production!)
    if settings.DEBUG:
        return {
            "message": "Verification code sent",
            "code": code,  # Only in development!
            "phone": data.phone
        }

    return {"message": "Verification code sent to your phone"}


@router.post("/verify-phone/confirm")
async def confirm_phone_verification(
    data: PhoneVerificationConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm phone verification with code

    Updates user's phone number and marks as verified
    """
    # Check if code exists and matches
    stored_data = verification_codes.get(data.phone)

    if not stored_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code not found or expired"
        )

    if stored_data["code"] != data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    if stored_data["user_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification code does not belong to current user"
        )

    # Update user's phone
    phone_hash = hash_phone_number(data.phone)
    current_user.phone_hash = phone_hash
    current_user.phone_verified = True

    await db.commit()

    # Remove used code
    del verification_codes[data.phone]

    return {"message": "Phone verified successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user

    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint is for consistency.
    """
    return {"message": "Logged out successfully"}
