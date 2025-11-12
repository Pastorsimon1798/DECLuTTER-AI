"""Database models for CommunityCircle"""

# Import all models here so Alembic can detect them
from app.models.user import User, UserProfile
from app.models.post import Post, Match, ContactToken
from app.models.notification import Notification, ActivityLog, Report
from app.models.shift import Organization, Shift, ShiftSignup

# Models for other projects will be imported as they're created
# from app.models.pod import Pod, PodMembership, PodPost, CheckInSchedule, CheckInResponse
# from app.models.resource import ResourceListing, ResourceBookmark

__all__ = [
    "User",
    "UserProfile",
    "Post",
    "Match",
    "ContactToken",
    "Notification",
    "ActivityLog",
    "Report",
    "Organization",
    "Shift",
    "ShiftSignup",
]
