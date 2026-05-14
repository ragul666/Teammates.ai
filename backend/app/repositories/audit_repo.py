"""Audit Log repository — DB access for audit entries."""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog, AuditAction


class AuditRepository:
    """Centralized database access for AuditLog model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization_id: uuid.UUID,
        action: AuditAction,
        actor_user_id: Optional[uuid.UUID] = None,
        work_item_id: Optional[uuid.UUID] = None,
        metadata_json: Optional[dict] = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            organization_id=organization_id,
            work_item_id=work_item_id,
            actor_user_id=actor_user_id,
            action=action,
            metadata_json=metadata_json,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_by_work_item(
        self, work_item_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[AuditLog]:
        """Get all audit logs for a specific work item."""
        result = await self.db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.actor))
            .where(
                AuditLog.work_item_id == work_item_id,
                AuditLog.organization_id == organization_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_list(
        self,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Get paginated audit logs for an organization."""
        count_query = (
            select(func.count(AuditLog.id))
            .where(AuditLog.organization_id == organization_id)
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(AuditLog)
            .options(selectinload(AuditLog.actor))
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())

        return items, total
