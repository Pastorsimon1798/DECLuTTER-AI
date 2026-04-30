"""User models - Shared authentication and user management"""
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class User(Base):
    """Core user model for authentication and basic profile"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pseudonym = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(255), unique=True, nullable=True)  # Optional for SMS-only users
    phone_hash = Column(String(64), unique=True, nullable=True, index=True)  # Hashed phone
    phone_verified = Column(Boolean, default=False)
    locale = Column(String(5), default="en")  # en, es, zh, etc.
    timezone = Column(String(50), default="America/New_York")

    # Notification preferences stored as JSONB
    notification_prefs = Column(
        JSONB,
        default={"sms": True, "email": True, "push": False},
        nullable=False
    )

    # Location (privacy-protected geohash)
    location_geohash = Column(String(12), nullable=True, index=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Hashed password (for web login)
    hashed_password = Column(String(255), nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author", foreign_keys="Post.author_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    # More relationships will be added as we create other models

    def __repr__(self):
        return f"<User {self.pseudonym}>"


class UserProfile(Base):
    """Extended user profile with optional enriched information"""

    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio = Column(Text, nullable=True)
    skills = Column(ARRAY(Text), default=list)  # ['cooking', 'driving', 'childcare']
    languages = Column(ARRAY(String(5)), default=list)  # ['en', 'es']
    accessibility_needs = Column(ARRAY(Text), default=list)
    avatar_url = Column(String(500), nullable=True)
    pronouns = Column(String(20), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile for user_id={self.user_id}>"
