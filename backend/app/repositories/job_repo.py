"""Background Job repository — DB access for async jobs."""

import uuid
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob, JobStatus


class JobRepository:
    """Centralized database access for BackgroundJob model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization_id: uuid.UUID,
        work_item_id: uuid.UUID,
        job_type: str = "send_email",
    ) -> BackgroundJob:
        """Create a new background job."""
        job = BackgroundJob(
            organization_id=organization_id,
            work_item_id=work_item_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_by_id(
        self, job_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[BackgroundJob]:
        """Get a job by ID, scoped to organization."""
        result = await self.db.execute(
            select(BackgroundJob).where(
                BackgroundJob.id == job_id,
                BackgroundJob.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_work_item(
        self, work_item_id: uuid.UUID, organization_id: uuid.UUID
    ) -> list[BackgroundJob]:
        """Get all jobs for a work item."""
        result = await self.db.execute(
            select(BackgroundJob)
            .where(
                BackgroundJob.work_item_id == work_item_id,
                BackgroundJob.organization_id == organization_id,
            )
            .order_by(BackgroundJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
    ) -> Optional[BackgroundJob]:
        """Update job status."""
        result = await self.db.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = status
            if status == JobStatus.PROCESSING:
                job.started_at = datetime.now(timezone.utc)
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now(timezone.utc)
            if error_message:
                job.error_message = error_message
            await self.db.flush()
        return job
