"""Notification models - Unified notification system for all features"""
from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Notification(Base):
    """Unified notifications table for all features"""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Recipient
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification details
    type = Column(String(50), nullable=False)  # 'match_found', 'shift_reminder', 'pod_sos', etc.
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)  # Deep link into app

    # Delivery channels
    channels = Column(ARRAY(String(20)), default=["in_app"], nullable=False)  # ['in_app', 'sms', 'email', 'push']

    # Status
    status = Column(String(20), default="pending", nullable=False, index=True)  # 'pending', 'sent', 'failed', 'read'

    # Timestamps
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'sent', 'failed', 'read')", name="check_notification_status"),
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.type} to {self.user_id} - {self.status}>"


class ActivityLog(Base):
    """Privacy-safe activity log for analytics"""

    __tablename__ = "activity_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User (nullable for privacy)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # 'post_created', 'shift_signup', 'pod_joined'
    event_data = Column(Text, nullable=True)  # Minimal, anonymized context (JSON string)

    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<ActivityLog {self.event_type} at {self.created_at}>"


class Report(Base):
    """Generic reports/flags for moderation"""

    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reporter
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Reported entities (one of these will be set)
    reported_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reported_post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=True)
    # More reported entities will be added as we create models for pods, etc.

    # Report details
    reason = Column(String(50), nullable=False)  # 'spam', 'harassment', 'inappropriate', 'other'
    description = Column(Text, nullable=True)

    # Status and resolution
    status = Column(String(20), default="pending", nullable=False, index=True)  # 'pending', 'investigating', 'resolved', 'dismissed'
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)  # Internal notes for moderators

    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("reason IN ('spam', 'harassment', 'inappropriate', 'other')", name="check_report_reason"),
        CheckConstraint("status IN ('pending', 'investigating', 'resolved', 'dismissed')", name="check_report_status"),
    )

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    reported_post = relationship("Post", foreign_keys=[reported_post_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<Report {self.reason} - {self.status}>"
