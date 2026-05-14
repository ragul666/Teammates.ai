"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import DbSession, CurrentUser
from app.schemas.auth import LoginRequest, LoginResponse, UserBasic
from app.services.auth_service import AuthService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: DbSession,
):
    """Authenticate a user and return a JWT token."""
    auth_service = AuthService(db)
    return await auth_service.login(body.email, body.password)


@router.get("/me", response_model=UserBasic)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """Get the current authenticated user's information."""
    return UserBasic(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        organization_id=str(current_user.organization_id),
        organization_name=current_user.organization.name,
    )
