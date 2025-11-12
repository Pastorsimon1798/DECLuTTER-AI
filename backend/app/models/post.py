"""Post models for Project 1: Needs & Offers Board"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import uuid
from app.database import Base


class Post(Base):
    """Needs and offers posted by users"""

    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Type and category
    type = Column(String(10), nullable=False)  # 'NEED' or 'OFFER'
    category = Column(String(50), nullable=False, index=True)  # 'food', 'transport', 'housing', etc.

    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Location (privacy-protected)
    location_geohash = Column(String(12), nullable=False, index=True)
    location_point = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)  # Internal only

    # Search radius
    radius_meters = Column(Integer, default=1000, nullable=False)

    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Visibility and status
    visibility = Column(String(20), default="public", nullable=False)  # 'public', 'circles', 'private'
    status = Column(String(20), default="open", nullable=False, index=True)  # 'open', 'matched', 'in_progress', 'completed', 'cancelled'

    # Timestamps
    expires_at = Column(TIMESTAMP(timezone=True), default=func.now() + func.cast('30 days', type_=String), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('NEED', 'OFFER')", name="check_post_type"),
        CheckConstraint("visibility IN ('public', 'circles', 'private')", name="check_post_visibility"),
        CheckConstraint("status IN ('open', 'matched', 'in_progress', 'completed', 'cancelled')", name="check_post_status"),
    )

    # Relationships
    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    matches = relationship("Match", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post {self.type} - {self.title[:30]}>"


class Match(Base):
    """Matches between needs and offers"""

    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Related post and users
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False, index=True)
    responder_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Denormalized

    # Match details
    method = Column(String(20), default="in_app", nullable=False)  # 'in_app', 'sms', 'phone'
    status = Column(String(20), default="pending", nullable=False)  # 'pending', 'accepted', 'declined', 'completed', 'cancelled'
    notes = Column(Text, nullable=True)

    # Timestamps
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("method IN ('in_app', 'sms', 'phone')", name="check_match_method"),
        CheckConstraint("status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled')", name="check_match_status"),
    )

    # Relationships
    post = relationship("Post", back_populates="matches")
    responder = relationship("User", foreign_keys=[responder_id])
    requester = relationship("User", foreign_keys=[requester_id])

    def __repr__(self):
        return f"<Match {self.id} - {self.status}>"


class ContactToken(Base):
    """Encrypted contact information tokens for consented sharing"""

    __tablename__ = "contact_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Owner of the contact info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Type and encrypted value
    kind = Column(String(20), nullable=False)  # 'phone', 'email', 'signal', 'whatsapp'
    encrypted_value = Column(Text, nullable=False)  # Encrypted contact info

    # Sharing context
    shared_with_user = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Who has access
    shared_via_post = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=True)  # Context of sharing

    # Expiration
    expires_at = Column(TIMESTAMP(timezone=True), default=func.now() + func.cast('7 days', type_=String), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("kind IN ('phone', 'email', 'signal', 'whatsapp')", name="check_contact_kind"),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    shared_with = relationship("User", foreign_keys=[shared_with_user])
    post = relationship("Post", foreign_keys=[shared_via_post])

    def __repr__(self):
        return f"<ContactToken {self.kind} for user {self.user_id}>"
