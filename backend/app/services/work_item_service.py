"""Work Item service — business logic for the sales workflow."""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, BadRequestError, ConflictError
from app.models.audit_log import AuditAction
from app.models.work_item import LeadWorkItem, WorkItemStatus
from app.models.user import User, UserRole
from app.repositories.work_item_repo import WorkItemRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.job_repo import JobRepository
from app.services.llm_service import get_llm_provider
from app.schemas.work_item import WorkItemResponse, WorkItemListResponse, DashboardStats


class WorkItemService:
    """Business logic for the lead work item workflow."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.work_item_repo = WorkItemRepository(db)
        self.audit_repo = AuditRepository(db)
        self.job_repo = JobRepository(db)

    def _to_response(self, item: LeadWorkItem) -> WorkItemResponse:
        """Convert a work item model to response schema."""
        return WorkItemResponse(
            id=str(item.id),
            organization_id=str(item.organization_id),
            assigned_reviewer_id=str(item.assigned_reviewer_id) if item.assigned_reviewer_id else None,
            assigned_reviewer_name=item.assigned_reviewer.name if item.assigned_reviewer else None,
            lead_name=item.lead_name,
            company_name=item.company_name,
            lead_context=item.lead_context,
            original_input=item.original_input,
            ai_output=item.ai_output,
            edited_output=item.edited_output,
            status=item.status.value,
            reviewer_note=item.reviewer_note,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    async def get_work_items(
        self,
        user: User,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> WorkItemListResponse:
        """Get work items list, filtered by role."""
        status_enum = WorkItemStatus(status) if status else None

        # Reviewers only see their assigned items
        reviewer_id = None
        if user.role == UserRole.REVIEWER:
            reviewer_id = user.id

        items, total = await self.work_item_repo.get_list(
            organization_id=user.organization_id,
            status=status_enum,
            assigned_reviewer_id=reviewer_id,
            page=page,
            page_size=page_size,
        )

        return WorkItemListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_work_item(
        self, item_id: uuid.UUID, user: User
    ) -> WorkItemResponse:
        """Get a single work item with authorization checks."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        # Reviewers can only access their assigned items
        if user.role == UserRole.REVIEWER and item.assigned_reviewer_id != user.id:
            raise NotFoundError("Work item not found")

        return self._to_response(item)

    async def update_draft(
        self,
        item_id: uuid.UUID,
        user: User,
        edited_output: str,
    ) -> WorkItemResponse:
        """Update the draft content of a work item."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        if user.role == UserRole.REVIEWER and item.assigned_reviewer_id != user.id:
            raise NotFoundError("Work item not found")

        if item.status not in (WorkItemStatus.PENDING_REVIEW,):
            raise BadRequestError("Can only edit items in pending review status")

        item.edited_output = edited_output
        await self.work_item_repo.update(item)

        # Audit log
        await self.audit_repo.create(
            organization_id=user.organization_id,
            action=AuditAction.DRAFT_EDITED,
            actor_user_id=user.id,
            work_item_id=item.id,
            metadata_json={"edited_length": len(edited_output)},
        )

        return self._to_response(item)

    async def approve_work_item(
        self,
        item_id: uuid.UUID,
        user: User,
        note: Optional[str] = None,
        edited_output: Optional[str] = None,
    ) -> WorkItemResponse:
        """Approve a work item and trigger background processing."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        if user.role == UserRole.REVIEWER and item.assigned_reviewer_id != user.id:
            raise NotFoundError("Work item not found")

        # Prevent duplicate approvals
        if item.status != WorkItemStatus.PENDING_REVIEW:
            raise ConflictError(
                f"Cannot approve item with status '{item.status.value}'. "
                "Only items in 'pending_review' status can be approved."
            )

        # Save any last-minute edits
        if edited_output:
            item.edited_output = edited_output

        # Update status
        item.status = WorkItemStatus.APPROVED
        item.reviewer_note = note
        await self.work_item_repo.update(item)

        # Create background job
        job = await self.job_repo.create(
            organization_id=user.organization_id,
            work_item_id=item.id,
            job_type="send_email",
        )

        # Audit log
        await self.audit_repo.create(
            organization_id=user.organization_id,
            action=AuditAction.ITEM_APPROVED,
            actor_user_id=user.id,
            work_item_id=item.id,
            metadata_json={"note": note, "job_id": str(job.id)},
        )

        # Commit so the Celery worker can read the data
        await self.db.commit()

        # Trigger Celery task
        from app.workers.tasks import process_approved_item
        process_approved_item.delay(str(job.id), str(item.id), str(user.organization_id))

        return self._to_response(item)

    async def reject_work_item(
        self,
        item_id: uuid.UUID,
        user: User,
        note: Optional[str] = None,
    ) -> WorkItemResponse:
        """Reject a work item."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        if user.role == UserRole.REVIEWER and item.assigned_reviewer_id != user.id:
            raise NotFoundError("Work item not found")

        if item.status != WorkItemStatus.PENDING_REVIEW:
            raise ConflictError(
                f"Cannot reject item with status '{item.status.value}'. "
                "Only items in 'pending_review' status can be rejected."
            )

        item.status = WorkItemStatus.REJECTED
        item.reviewer_note = note
        await self.work_item_repo.update(item)

        # Audit log
        await self.audit_repo.create(
            organization_id=user.organization_id,
            action=AuditAction.ITEM_REJECTED,
            actor_user_id=user.id,
            work_item_id=item.id,
            metadata_json={"note": note},
        )

        return self._to_response(item)

    async def regenerate_draft(
        self, item_id: uuid.UUID, user: User
    ) -> WorkItemResponse:
        """Regenerate the AI draft for a work item."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        if user.role == UserRole.REVIEWER and item.assigned_reviewer_id != user.id:
            raise NotFoundError("Work item not found")

        if item.status not in (WorkItemStatus.PENDING_REVIEW, WorkItemStatus.REJECTED):
            raise BadRequestError(
                "Can only regenerate drafts for items in pending review or rejected status"
            )

        try:
            # Generate new draft via LLM (inline async call)
            llm = get_llm_provider()
            new_draft = await llm.generate_follow_up(
                lead_name=item.lead_name,
                company_name=item.company_name,
                lead_context=item.lead_context,
                original_input=item.original_input,
            )

            # Update item with new draft
            item.ai_output = new_draft
            item.edited_output = None  # Clear previous edits
            item.status = WorkItemStatus.PENDING_REVIEW
            await self.work_item_repo.update(item)

            # Audit log
            await self.audit_repo.create(
                organization_id=user.organization_id,
                action=AuditAction.DRAFT_REGENERATED,
                actor_user_id=user.id,
                work_item_id=item.id,
                metadata_json={"draft_length": len(new_draft)},
            )

        except Exception as e:
            raise BadRequestError(f"Failed to regenerate draft: {str(e)}")

        return self._to_response(item)

    async def get_dashboard_stats(self, user: User) -> DashboardStats:
        """Get dashboard statistics for the organization."""
        stats = await self.work_item_repo.get_stats(user.organization_id)
        return DashboardStats(
            total_items=stats.get("total", 0),
            pending_review=stats.get("pending_review", 0),
            approved=stats.get("approved", 0),
            rejected=stats.get("rejected", 0),
            processing=stats.get("processing", 0),
            sent=stats.get("sent", 0),
            failed=stats.get("failed", 0),
        )

    async def retry_failed_item(
        self, item_id: uuid.UUID, user: User
    ) -> WorkItemResponse:
        """Retry a failed work item by creating a new background job."""
        item = await self.work_item_repo.get_by_id(item_id, user.organization_id)
        if not item:
            raise NotFoundError("Work item not found")

        if item.status != WorkItemStatus.FAILED:
            raise BadRequestError("Can only retry failed items")

        # Reset status
        item.status = WorkItemStatus.APPROVED
        await self.work_item_repo.update(item)

        # Create new job
        job = await self.job_repo.create(
            organization_id=user.organization_id,
            work_item_id=item.id,
            job_type="send_email",
        )

        # Audit
        await self.audit_repo.create(
            organization_id=user.organization_id,
            action=AuditAction.ITEM_APPROVED,
            actor_user_id=user.id,
            work_item_id=item.id,
            metadata_json={"note": "Retry after failure", "job_id": str(job.id)},
        )

        await self.db.commit()

        from app.workers.tasks import process_approved_item
        process_approved_item.delay(str(job.id), str(item.id), str(user.organization_id))

        return self._to_response(item)
