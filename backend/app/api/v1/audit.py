"""Audit Log endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Get paginated audit logs for the organization."""
    repo = AuditRepository(db)
    items, total = await repo.get_list(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                organization_id=str(log.organization_id),
                work_item_id=str(log.work_item_id) if log.work_item_id else None,
                actor_user_id=str(log.actor_user_id) if log.actor_user_id else None,
                actor_name=log.actor.name if log.actor else "System",
                action=log.action.value,
                metadata_json=log.metadata_json,
                created_at=log.created_at,
            )
            for log in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/work-item/{work_item_id}")
async def get_work_item_audit_logs(
    work_item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get audit logs for a specific work item."""
    repo = AuditRepository(db)
    logs = await repo.get_by_work_item(work_item_id, current_user.organization_id)

    return [
        AuditLogResponse(
            id=str(log.id),
            organization_id=str(log.organization_id),
            work_item_id=str(log.work_item_id) if log.work_item_id else None,
            actor_user_id=str(log.actor_user_id) if log.actor_user_id else None,
            actor_name=log.actor.name if log.actor else "System",
            action=log.action.value,
            metadata_json=log.metadata_json,
            created_at=log.created_at,
        )
        for log in logs
    ]
