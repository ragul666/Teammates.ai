"""Admin-only endpoints."""

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.services.work_item_service import WorkItemService
from app.repositories.user_repo import UserRepository
from app.schemas.work_item import DashboardStats
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: AdminUser,
    db: DbSession,
):
    """Get dashboard statistics for the organization.

    Admin-only endpoint — server-side role check via AdminUser dependency.
    """
    service = WorkItemService(db)
    return await service.get_dashboard_stats(current_user)


@router.get("/users", response_model=list[UserResponse])
async def list_organization_users(
    current_user: AdminUser,
    db: DbSession,
):
    """List all users in the organization.

    Admin-only endpoint.
    """
    repo = UserRepository(db)
    users = await repo.get_by_org(current_user.organization_id)
    return [
        UserResponse(
            id=str(u.id),
            name=u.name,
            email=u.email,
            role=u.role.value,
            organization_id=str(u.organization_id),
            created_at=u.created_at,
        )
        for u in users
    ]
