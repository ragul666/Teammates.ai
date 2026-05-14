"""API dependencies — authentication, DB session, authorization."""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository


async def get_current_user(
    authorization: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT token.

    This is the core authentication dependency. Every protected
    endpoint uses this to verify the caller's identity.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError(detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedError(detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError(detail="Invalid token payload")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise UnauthorizedError(detail="User not found")

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(detail="Admin access required")
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
