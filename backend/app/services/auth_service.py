"""Authentication service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginResponse, UserBasic


class AuthService:
    """Handles authentication logic."""

    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def login(self, email: str, password: str) -> LoginResponse:
        """Authenticate a user and return a JWT token."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedError(detail="Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedError(detail="Invalid email or password")

        # Create JWT token with user and org info
        token = create_access_token(
            data={
                "sub": str(user.id),
                "org_id": str(user.organization_id),
                "role": user.role.value,
            }
        )

        return LoginResponse(
            access_token=token,
            user=UserBasic(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role.value,
                organization_id=str(user.organization_id),
                organization_name=user.organization.name,
            ),
        )
