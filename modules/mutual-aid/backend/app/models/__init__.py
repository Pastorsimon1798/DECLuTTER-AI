"""Database models for CommunityCircle"""

# Import all models here so Alembic can detect them
from app.models.user import User, UserProfile
from app.models.post import Post, Match, ContactToken
from app.models.notification import Notification, ActivityLog, Report
from app.models.shift import Organization, Shift, ShiftSignup
from app.models.resource import ResourceListing, ResourceBookmark
from app.models.pod import Pod, PodMember, CheckIn, SOSBroadcast, PodPost

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
    "ResourceListing",
    "ResourceBookmark",
    "Pod",
    "PodMember",
    "CheckIn",
    "SOSBroadcast",
    "PodPost",
]
