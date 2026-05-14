"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    user: "UserBasic"


class UserBasic(BaseModel):
    """Basic user info returned after login."""
    id: str
    name: str
    email: str
    role: str
    organization_id: str
    organization_name: str

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # user_id
    org_id: str  # organization_id
    role: str  # user role
    exp: int | None = None


# Update forward reference
LoginResponse.model_rebuild()
