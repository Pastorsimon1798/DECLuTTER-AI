from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class PodMemberRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class PodMemberStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"


class CheckInStatus(str, Enum):
    DOING_WELL = "doing_well"
    NEED_SUPPORT = "need_support"
    EMERGENCY = "emergency"


class SOSUrgency(str, Enum):
    HIGH = "high"
    CRITICAL = "critical"


class PodPostType(str, Enum):
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    QUESTION = "question"
    RESOURCE = "resource"


# Pod Schemas
class PodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_private: bool = True
    max_members: int = Field(default=20, ge=2, le=100)
    check_in_frequency_days: int = Field(default=7, ge=1, le=30)
    enable_wellness_alerts: bool = True
    missed_checkins_threshold: int = Field(default=2, ge=1, le=10)
    enable_sos_broadcasts: bool = True

    class Config:
        from_attributes = True


class PodCreate(PodBase):
    pass


class PodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_private: Optional[bool] = None
    max_members: Optional[int] = Field(None, ge=2, le=100)
    check_in_frequency_days: Optional[int] = Field(None, ge=1, le=30)
    enable_wellness_alerts: Optional[bool] = None
    missed_checkins_threshold: Optional[int] = Field(None, ge=1, le=10)
    enable_sos_broadcasts: Optional[bool] = None

    class Config:
        from_attributes = True


class PodResponse(PodBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: int = 0  # Will be calculated
    my_role: Optional[str] = None  # Will be set based on current user

    class Config:
        from_attributes = True


# Pod Member Schemas
class PodMemberBase(BaseModel):
    role: str = "member"

    class Config:
        from_attributes = True


class PodMemberCreate(BaseModel):
    user_id: Optional[UUID] = None  # For admin inviting someone
    # If user_id not provided, assumes current user


class PodMemberUpdate(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class PodMemberResponse(PodMemberBase):
    id: UUID
    pod_id: UUID
    user_id: UUID
    status: str
    last_check_in_at: Optional[datetime] = None
    consecutive_missed_checkins: int = 0
    joined_at: datetime
    updated_at: Optional[datetime] = None

    # User info (will be populated)
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


# Check-In Schemas
class CheckInBase(BaseModel):
    status: str
    message: Optional[str] = None
    is_private: bool = False

    class Config:
        from_attributes = True


class CheckInCreate(CheckInBase):
    pass


class CheckInResponse(CheckInBase):
    id: UUID
    pod_id: UUID
    user_id: UUID
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# SOS Broadcast Schemas
class SOSBroadcastBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    urgency: str = "high"
    location: Optional[str] = None

    class Config:
        from_attributes = True


class SOSBroadcastCreate(SOSBroadcastBase):
    pass


class SOSBroadcastUpdate(BaseModel):
    is_resolved: bool

    class Config:
        from_attributes = True


class SOSBroadcastResponse(SOSBroadcastBase):
    id: UUID
    pod_id: UUID
    user_id: UUID
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# Pod Post Schemas
class PodPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    post_type: str = "general"

    class Config:
        from_attributes = True


class PodPostCreate(PodPostBase):
    pass


class PodPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    post_type: Optional[str] = None
    is_pinned: Optional[bool] = None

    class Config:
        from_attributes = True


class PodPostResponse(PodPostBase):
    id: UUID
    pod_id: UUID
    user_id: UUID
    is_pinned: bool
    pinned_by: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# Wellness Alert Schema
class WellnessAlert(BaseModel):
    """Schema for wellness alerts about members who haven't checked in"""
    member_id: UUID
    user_id: UUID
    user_name: str
    last_check_in_at: Optional[datetime] = None
    consecutive_missed_checkins: int
    days_since_last_checkin: Optional[int] = None
