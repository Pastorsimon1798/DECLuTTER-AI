"""Pydantic schemas for Post models (Project 1: Needs & Offers Board)"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class PostType(str, Enum):
    """Enum for post types"""
    NEED = "NEED"
    OFFER = "OFFER"


class PostStatus(str, Enum):
    """Enum for post status"""
    OPEN = "open"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PostVisibility(str, Enum):
    """Enum for post visibility"""
    PUBLIC = "public"
    CIRCLES = "circles"
    PRIVATE = "private"


class LocationInput(BaseModel):
    """Schema for location input (lat/lon)"""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class PostBase(BaseModel):
    """Base schema for posts"""
    type: PostType
    category: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    radius_meters: int = Field(default=1000, ge=100, le=804672)  # up to 500 miles
    visibility: PostVisibility = Field(default=PostVisibility.PUBLIC)


class PostCreate(PostBase):
    """Schema for creating a new post"""
    location: LocationInput

    @validator('category')
    def category_lowercase(cls, v):
        """Convert category to lowercase"""
        return v.lower().strip()


class PostUpdate(BaseModel):
    """Schema for updating a post"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[PostStatus] = None
    radius_meters: Optional[int] = Field(None, ge=100, le=804672)  # up to 500 miles
    visibility: Optional[PostVisibility] = None


class PostResponse(PostBase):
    """Schema for post response"""
    id: uuid.UUID
    author_id: uuid.UUID
    author_pseudonym: str  # Denormalized for easy access
    location_geohash: str
    status: PostStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    distance_meters: Optional[int] = None  # Calculated distance from user

    class Config:
        from_attributes = True


class PostSearchParams(BaseModel):
    """Schema for post search parameters"""
    type: Optional[PostType] = None
    category: Optional[str] = None
    location: Optional[LocationInput] = None
    radius_meters: int = Field(default=5000, ge=100, le=804672)  # up to 500 miles
    status: PostStatus = Field(default=PostStatus.OPEN)
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MatchStatus(str, Enum):
    """Enum for match status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchCreate(BaseModel):
    """Schema for creating a match (responding to a post)"""
    post_id: uuid.UUID
    method: str = Field(default="in_app", pattern="^(in_app|sms|phone)$")
    notes: Optional[str] = Field(None, max_length=500)


class MatchUpdate(BaseModel):
    """Schema for updating a match"""
    status: MatchStatus
    notes: Optional[str] = Field(None, max_length=500)


class MatchResponse(BaseModel):
    """Schema for match response"""
    id: uuid.UUID
    post_id: uuid.UUID
    post_title: str  # Denormalized
    responder_id: uuid.UUID
    responder_pseudonym: str  # Denormalized
    requester_id: uuid.UUID
    requester_pseudonym: str  # Denormalized
    method: str
    status: MatchStatus
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactTokenCreate(BaseModel):
    """Schema for creating a contact token (sharing contact info)"""
    user_id: uuid.UUID
    kind: str = Field(..., pattern="^(phone|email|signal|whatsapp)$")
    value: str  # Will be encrypted before storage
    shared_with_user: uuid.UUID
    shared_via_post: Optional[uuid.UUID] = None


class ContactTokenResponse(BaseModel):
    """Schema for contact token response"""
    id: uuid.UUID
    kind: str
    value: str  # Decrypted value (only for authorized users)
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
