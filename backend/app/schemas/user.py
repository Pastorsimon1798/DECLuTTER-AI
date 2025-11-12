"""Pydantic schemas for User models"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    pseudonym: str = Field(..., min_length=3, max_length=50, description="User's display name")
    email: Optional[EmailStr] = None
    locale: str = Field(default="en", pattern="^[a-z]{2}$")
    timezone: str = Field(default="America/New_York", max_length=50)
    location_geohash: Optional[str] = Field(None, max_length=12)


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    pseudonym: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    password: Optional[str] = Field(None, min_length=8)
    locale: str = Field(default="en")
    timezone: str = Field(default="America/New_York")

    @validator('pseudonym')
    def pseudonym_alphanumeric(cls, v):
        """Ensure pseudonym contains only letters, numbers, and underscores"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Pseudonym must contain only letters, numbers, underscores, and hyphens')
        return v

    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # Can be email, phone, or pseudonym
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    pseudonym: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    locale: Optional[str] = Field(None, pattern="^[a-z]{2}$")
    timezone: Optional[str] = None
    location_geohash: Optional[str] = None
    notification_prefs: Optional[Dict[str, bool]] = None


class UserResponse(BaseModel):
    """Schema for user response (public info)"""
    id: uuid.UUID
    pseudonym: str
    email: Optional[str] = None
    locale: str
    timezone: str
    location_geohash: Optional[str] = None
    notification_prefs: Dict[str, bool]
    phone_verified: bool
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Base schema for user profile"""
    bio: Optional[str] = Field(None, max_length=500)
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    accessibility_needs: List[str] = Field(default_factory=list)
    pronouns: Optional[str] = Field(None, max_length=20)


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile"""
    pass


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response"""
    user_id: uuid.UUID
    avatar_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PhoneVerificationRequest(BaseModel):
    """Schema for requesting phone verification"""
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")


class PhoneVerificationConfirm(BaseModel):
    """Schema for confirming phone verification"""
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    code: str = Field(..., min_length=6, max_length=6)


class TokenData(BaseModel):
    """Schema for data stored in JWT token"""
    user_id: Optional[str] = None
