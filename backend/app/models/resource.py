from sqlalchemy import Column, String, Text, ForeignKey, CheckConstraint, ARRAY, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
import uuid

from app.database import Base


class ResourceListing(Base):
    """Cache of 211 API data for pantries and other resources"""
    __tablename__ = "resource_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(200), unique=True)  # ID from 211 API
    name = Column(String(300), nullable=False)
    category = Column(String(50), nullable=False)  # Main category: 'food', 'shelter', 'healthcare', etc.
    subcategory = Column(String(100))  # Detailed subcategory
    description = Column(Text)
    location_address = Column(Text)
    location_point = Column(Geography("POINT", srid=4326))
    location_geohash = Column(String(12))
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(500))
    hours = Column(JSONB)  # Structured hours data
    services = Column(ARRAY(Text))
    languages = Column(ARRAY(String(5)))
    accessibility_features = Column(ARRAY(Text))
    eligibility_requirements = Column(Text)
    documents_required = Column(ARRAY(Text))

    # Phase 3.5: Community contributions and verification
    is_community_contributed = Column(Boolean, default=False, nullable=False)
    population_tags = Column(ARRAY(String(50)))  # 'veterans', 'lgbtq', 'families', 'immigrants', etc.
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at = Column(TIMESTAMP(timezone=True))
    verification_count = Column(Integer, default=0)  # Community verification count

    last_verified_at = Column(TIMESTAMP(timezone=True))
    cached_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    cache_expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    bookmarks = relationship("ResourceBookmark", back_populates="resource", cascade="all, delete-orphan")
    verifier = relationship("User", foreign_keys=[verified_by])

    def __repr__(self):
        return f"<ResourceListing {self.name}>"

    @property
    def is_cache_expired(self):
        return datetime.utcnow() > self.cache_expires_at if self.cache_expires_at else True


class ResourceBookmark(Base):
    """User bookmarks for resources"""
    __tablename__ = "resource_bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resource_listings.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    resource = relationship("ResourceListing", back_populates="bookmarks")

    __table_args__ = (
        CheckConstraint('user_id IS NOT NULL AND resource_id IS NOT NULL', name='resource_bookmark_check'),
    )

    def __repr__(self):
        return f"<ResourceBookmark {self.user_id} -> {self.resource_id}>"
