from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


# Phase 3.5: Expanded Categories and Population Tags
class ResourceCategory(str, Enum):
    """Main resource categories (Option A: 8-10 main categories)"""
    FOOD = "food"  # Pantries, meal programs, community fridges
    SHELTER = "shelter"  # Emergency, transitional, housing assistance
    HEALTHCARE = "healthcare"  # Medical, dental, mental health, prescriptions
    CLOTHING_HOUSEHOLD = "clothing_household"  # Clothing closets, furniture
    LEGAL = "legal"  # Legal aid, advocacy
    FINANCIAL = "financial"  # Financial assistance, benefits enrollment
    EMPLOYMENT_EDUCATION = "employment_education"  # Job training, education, childcare
    TRANSPORTATION = "transportation"  # Public transit assistance, rides


class PopulationTag(str, Enum):
    """Population-specific resource tags"""
    VETERANS = "veterans"
    LGBTQ = "lgbtq"
    FAMILIES = "families"
    IMMIGRANTS = "immigrants"
    DISABILITY_ACCESSIBLE = "disability_accessible"
    YOUTH = "youth"
    SENIORS = "seniors"


# Resource Listing Schemas
class ResourceListingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    category: str = Field(..., min_length=1, max_length=50)
    subcategory: Optional[str] = None
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
    population_tags: Optional[List[str]] = []

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
    lat: Optional[float] = None  # Extracted from location_point for map display
    lon: Optional[float] = None  # Extracted from location_point for map display
    last_verified_at: Optional[datetime] = None
    cached_at: datetime
    cache_expires_at: datetime
    created_at: datetime
    is_bookmarked: bool = False  # Will be set based on user
    bookmark_id: Optional[UUID] = None

    # Phase 3.5 fields
    is_community_contributed: bool = False
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    verification_count: int = 0

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
    subcategory: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius: Optional[int] = Field(default=5000, ge=100, le=804672)  # meters (up to 500 miles)
    open_now: bool = False  # Filter by currently open
    languages: Optional[List[str]] = None
    accessibility_features: Optional[List[str]] = None
    population_tags: Optional[List[str]] = None  # Phase 3.5
    is_community_contributed: Optional[bool] = None  # Filter by source

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


# Phase 3.5: Community Verification
class ResourceVerificationCreate(BaseModel):
    """Schema for community verification of resources"""
    is_accurate: bool
    notes: Optional[str] = None
