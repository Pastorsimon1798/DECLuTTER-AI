from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class ShiftStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SignupStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[dict] = None  # {lat: float, lon: float}

    class Config:
        use_enum_values = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[dict] = None

    class Config:
        use_enum_values = True


class OrganizationResponse(OrganizationBase):
    id: UUID
    location_geohash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True


# Shift Schemas
class ShiftBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    location_point: Optional[dict] = None  # {lat: float, lon: float}
    start_time: datetime
    end_time: datetime
    capacity: int = Field(default=1, ge=1)
    recurrence_rule: Optional[str] = None
    reminder_24h: bool = True
    reminder_2h: bool = True
    status: ShiftStatus = ShiftStatus.OPEN

    @validator('end_time')
    def end_time_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    class Config:
        use_enum_values = True


class ShiftCreate(ShiftBase):
    organization_id: UUID


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    location_point: Optional[dict] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=1)
    recurrence_rule: Optional[str] = None
    reminder_24h: Optional[bool] = None
    reminder_2h: Optional[bool] = None
    status: Optional[ShiftStatus] = None

    @validator('end_time')
    def end_time_after_start(cls, v, values):
        if 'start_time' in values and values['start_time'] and v and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    class Config:
        use_enum_values = True


class ShiftResponse(ShiftBase):
    id: UUID
    organization_id: UUID
    coordinator_id: Optional[UUID] = None
    filled_count: int = 0
    created_at: datetime
    updated_at: datetime
    available_spots: int = 0
    is_full: bool = False

    class Config:
        from_attributes = True
        use_enum_values = True


class ShiftWithOrganization(ShiftResponse):
    organization: OrganizationResponse

    class Config:
        from_attributes = True
        use_enum_values = True


# Shift Signup Schemas
class ShiftSignupBase(BaseModel):
    notes: Optional[str] = None


class ShiftSignupCreate(ShiftSignupBase):
    shift_id: UUID


class ShiftSignupUpdate(BaseModel):
    status: Optional[SignupStatus] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True


class ShiftSignupResponse(ShiftSignupBase):
    id: UUID
    shift_id: UUID
    volunteer_id: UUID
    status: SignupStatus
    reminder_24h_sent: bool = False
    reminder_2h_sent: bool = False
    signed_up_at: datetime
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class ShiftSignupWithDetails(ShiftSignupResponse):
    shift: ShiftWithOrganization

    class Config:
        from_attributes = True
        use_enum_values = True


# Search/Filter Schemas
class ShiftSearchParams(BaseModel):
    organization_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ShiftStatus] = None
    available_only: bool = False  # Only show shifts with available spots

    class Config:
        use_enum_values = True
