from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


# Resource Listing Schemas
class ResourceListingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    location_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[Dict] = None
    services: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    accessibility_features: Optional[List[str]] = []
    eligibility_requirements: Optional[str] = None
    documents_required: Optional[List[str]] = []

    class Config:
        from_attributes = True


class ResourceListingCreate(ResourceListingBase):
    external_id: Optional[str] = None
    location: Optional[dict] = None  # {lat: float, lon: float}
    last_verified_at: Optional[datetime] = None


class ResourceListingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    location_address: Optional[str] = None
    location: Optional[dict] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[Dict] = None
    services: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    accessibility_features: Optional[List[str]] = None
    eligibility_requirements: Optional[str] = None
    documents_required: Optional[List[str]] = None
    last_verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceListingResponse(ResourceListingBase):
    id: UUID
    external_id: Optional[str] = None
    location_geohash: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    cached_at: datetime
    cache_expires_at: datetime
    created_at: datetime
    is_bookmarked: bool = False  # Will be set based on user
    bookmark_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# Resource Bookmark Schemas
class ResourceBookmarkBase(BaseModel):
    notes: Optional[str] = None


class ResourceBookmarkCreate(ResourceBookmarkBase):
    resource_id: UUID


class ResourceBookmarkUpdate(BaseModel):
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ResourceBookmarkResponse(ResourceBookmarkBase):
    id: UUID
    resource_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceBookmarkWithDetails(ResourceBookmarkResponse):
    resource: ResourceListingResponse

    class Config:
        from_attributes = True


# Search/Filter Schemas
class ResourceSearchParams(BaseModel):
    query: Optional[str] = None  # Text search in name/description
    category: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius: Optional[int] = Field(default=5000, ge=100, le=50000)  # meters
    open_now: bool = False  # Filter by currently open
    languages: Optional[List[str]] = None
    accessibility_features: Optional[List[str]] = None

    class Config:
        from_attributes = True


# 211 API Integration Schemas
class OpenReferralLocation(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None


class OpenReferralService(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    application_process: Optional[str] = None
    eligibility_description: Optional[str] = None
    fees_description: Optional[str] = None
    languages: Optional[List[str]] = []


class OpenReferralOrganization(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    locations: Optional[List[OpenReferralLocation]] = []
    services: Optional[List[OpenReferralService]] = []
