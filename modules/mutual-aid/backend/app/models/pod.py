from sqlalchemy import Column, String, Text, ForeignKey, CheckConstraint, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Pod(Base):
    """Pod/Micro-Circle for close-knit mutual aid groups"""
    __tablename__ = "pods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Privacy settings
    is_private = Column(Boolean, default=True, nullable=False)  # Private pods require approval to join
    max_members = Column(Integer, default=20)  # Recommended max for close-knit groups

    # Check-in settings
    check_in_frequency_days = Column(Integer, default=7)  # How often members should check in
    enable_wellness_alerts = Column(Boolean, default=True)  # Alert if member misses check-ins
    missed_checkins_threshold = Column(Integer, default=2)  # Number of missed check-ins before alert

    # SOS settings
    enable_sos_broadcasts = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("PodMember", back_populates="pod", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="pod", cascade="all, delete-orphan")
    sos_broadcasts = relationship("SOSBroadcast", back_populates="pod", cascade="all, delete-orphan")
    pod_posts = relationship("PodPost", back_populates="pod", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pod {self.name}>"


class PodMember(Base):
    """Pod membership with roles and status"""
    __tablename__ = "pod_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pod_id = Column(UUID(as_uuid=True), ForeignKey("pods.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Role: admin (can manage pod), member (regular member)
    role = Column(String(20), default='member', nullable=False)

    # Status: pending (waiting approval), active, inactive (left pod)
    status = Column(String(20), default='pending', nullable=False)

    # Wellness tracking
    last_check_in_at = Column(TIMESTAMP(timezone=True))
    consecutive_missed_checkins = Column(Integer, default=0)

    joined_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pod = relationship("Pod", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    check_ins = relationship("CheckIn", back_populates="member", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("pod_id IS NOT NULL AND user_id IS NOT NULL", name="pod_member_check"),
    )

    def __repr__(self):
        return f"<PodMember {self.user_id} in {self.pod_id}>"


class CheckIn(Base):
    """Member wellness check-ins"""
    __tablename__ = "check_ins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pod_id = Column(UUID(as_uuid=True), ForeignKey("pods.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey("pod_members.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Wellness status
    status = Column(String(20), nullable=False)  # 'doing_well', 'need_support', 'emergency'
    message = Column(Text)  # Optional message
    is_private = Column(Boolean, default=False)  # Only visible to pod admins

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    pod = relationship("Pod", back_populates="check_ins")
    member = relationship("PodMember", back_populates="check_ins")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<CheckIn {self.user_id} - {self.status}>"


class SOSBroadcast(Base):
    """Emergency SOS broadcasts to pod members"""
    __tablename__ = "sos_broadcasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pod_id = Column(UUID(as_uuid=True), ForeignKey("pods.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    message = Column(Text, nullable=False)
    urgency = Column(String(20), default='high')  # 'high', 'critical'
    location = Column(Text)  # Optional location info

    # Status tracking
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(TIMESTAMP(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    pod = relationship("Pod", back_populates="sos_broadcasts")
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<SOSBroadcast {self.id} - {self.urgency}>"


class PodPost(Base):
    """Internal posts within a pod"""
    __tablename__ = "pod_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pod_id = Column(UUID(as_uuid=True), ForeignKey("pods.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String(20), default='general')  # 'general', 'announcement', 'question', 'resource'

    # Pinning for important posts
    is_pinned = Column(Boolean, default=False)
    pinned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pod = relationship("Pod", back_populates="pod_posts")
    user = relationship("User", foreign_keys=[user_id])
    pinner = relationship("User", foreign_keys=[pinned_by])

    def __repr__(self):
        return f"<PodPost {self.title}>"
