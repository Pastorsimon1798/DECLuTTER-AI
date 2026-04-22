from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiEnvelope(BaseModel):
    ok: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
