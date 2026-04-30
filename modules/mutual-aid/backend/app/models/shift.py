from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime
import uuid

from app.database import Base


class Organization(Base):
    """Organizations that create volunteer shifts"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    location_geohash = Column(String(12))
    location_point = Column(Geography("POINT", srid=4326))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    shifts = relationship("Shift", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name}>"


class Shift(Base):
    """Volunteer shifts"""
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    location = Column(String(500))  # Can be different from org location
    location_point = Column(Geography("POINT", srid=4326))
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    capacity = Column(Integer, nullable=False, default=1)  # How many volunteers needed
    filled_count = Column(Integer, default=0)  # Current sign-ups
    recurrence_rule = Column(Text)  # RRULE format for recurring shifts
    reminder_24h = Column(Boolean, default=True)
    reminder_2h = Column(Boolean, default=True)
    coordinator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(
        String(20),
        CheckConstraint("status IN ('draft', 'open', 'full', 'completed', 'cancelled')"),
        default='open',
        nullable=False
    )
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="shifts")
    coordinator = relationship("User", foreign_keys=[coordinator_id])
    signups = relationship("ShiftSignup", back_populates="shift", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shift {self.name} at {self.start_time}>"

    @property
    def is_full(self):
        return self.filled_count >= self.capacity

    @property
    def available_spots(self):
        return max(0, self.capacity - self.filled_count)


class ShiftSignup(Base):
    """Volunteer sign-ups for shifts"""
    __tablename__ = "shift_signups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_id = Column(UUID(as_uuid=True), ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(
        String(20),
        CheckConstraint("status IN ('confirmed', 'cancelled', 'no_show', 'completed')"),
        default='confirmed',
        nullable=False
    )
    notes = Column(Text)
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_2h_sent = Column(Boolean, default=False)
    signed_up_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    cancelled_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    # Relationships
    shift = relationship("Shift", back_populates="signups")
    volunteer = relationship("User", foreign_keys=[volunteer_id])

    __table_args__ = (
        # Unique constraint: one user can't sign up for same shift twice
        CheckConstraint('shift_id IS NOT NULL AND volunteer_id IS NOT NULL', name='shift_signup_check'),
    )

    def __repr__(self):
        return f"<ShiftSignup {self.volunteer_id} for shift {self.shift_id}>"
