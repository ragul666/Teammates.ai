"""User schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    name: str
    email: str
    role: str
    organization_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
