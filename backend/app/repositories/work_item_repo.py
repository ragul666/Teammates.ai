"""Work Item repository — DB access for lead work items."""

import uuid
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.work_item import LeadWorkItem, WorkItemStatus


class WorkItemRepository:
    """Centralized database access for LeadWorkItem model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, item_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[LeadWorkItem]:
        """Get a work item by ID, scoped to organization."""
        result = await self.db.execute(
            select(LeadWorkItem)
            .options(selectinload(LeadWorkItem.assigned_reviewer))
            .where(
                LeadWorkItem.id == item_id,
                LeadWorkItem.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        organization_id: uuid.UUID,
        status: Optional[WorkItemStatus] = None,
        assigned_reviewer_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LeadWorkItem], int]:
        """Get paginated list of work items, scoped to organization."""
        query = (
            select(LeadWorkItem)
            .options(selectinload(LeadWorkItem.assigned_reviewer))
            .where(LeadWorkItem.organization_id == organization_id)
        )
        count_query = (
            select(func.count(LeadWorkItem.id))
            .where(LeadWorkItem.organization_id == organization_id)
        )

        if status:
            query = query.where(LeadWorkItem.status == status)
            count_query = count_query.where(LeadWorkItem.status == status)

        if assigned_reviewer_id:
            query = query.where(
                LeadWorkItem.assigned_reviewer_id == assigned_reviewer_id
            )
            count_query = count_query.where(
                LeadWorkItem.assigned_reviewer_id == assigned_reviewer_id
            )

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get items with pagination
        offset = (page - 1) * page_size
        query = query.order_by(LeadWorkItem.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_status(
        self,
        item_id: uuid.UUID,
        organization_id: uuid.UUID,
        status: WorkItemStatus,
    ) -> Optional[LeadWorkItem]:
        """Update work item status."""
        item = await self.get_by_id(item_id, organization_id)
        if item:
            item.status = status
            await self.db.flush()
        return item

    async def update(self, item: LeadWorkItem) -> LeadWorkItem:
        """Save changes to a work item."""
        await self.db.flush()
        return item

    async def get_stats(self, organization_id: uuid.UUID) -> dict:
        """Get work item statistics for an organization."""
        result = await self.db.execute(
            select(LeadWorkItem.status, func.count(LeadWorkItem.id))
            .where(LeadWorkItem.organization_id == organization_id)
            .group_by(LeadWorkItem.status)
        )
        stats = {status.value: 0 for status in WorkItemStatus}
        total = 0
        for status, count in result.all():
            stats[status.value] = count
            total += count
        stats["total"] = total
        return stats
