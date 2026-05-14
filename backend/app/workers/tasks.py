"""Celery tasks — background job processing.

This module handles asynchronous processing after a reviewer approves a work item:
1. Marks the job as processing
2. Simulates sending the email
3. Simulates CRM sync
4. Creates activity records
5. Updates work item status to Sent or Failed
6. Logs every step in the audit trail
"""

import time
import uuid
import random
import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.workers.celery_app import celery_app
from app.config import settings
from app.models.work_item import LeadWorkItem, WorkItemStatus
from app.models.background_job import BackgroundJob, JobStatus
from app.models.audit_log import AuditLog, AuditAction

logger = logging.getLogger(__name__)

# Sync engine for Celery workers (Celery doesn't support async)
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
SyncSessionFactory = sessionmaker(bind=sync_engine)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="process_approved_item",
)
def process_approved_item(
    self,
    job_id: str,
    work_item_id: str,
    organization_id: str,
):
    """Process an approved work item.

    Steps:
    1. Mark job as processing
    2. Update work item status to processing
    3. Simulate email sending
    4. Simulate CRM sync
    5. Update statuses to completed/sent
    6. Create audit log entries
    """
    db = SyncSessionFactory()
    try:
        job_uuid = uuid.UUID(job_id)
        item_uuid = uuid.UUID(work_item_id)
        org_uuid = uuid.UUID(organization_id)

        # Fetch job and work item
        job = db.query(BackgroundJob).filter(
            BackgroundJob.id == job_uuid,
            BackgroundJob.organization_id == org_uuid,
        ).first()

        work_item = db.query(LeadWorkItem).filter(
            LeadWorkItem.id == item_uuid,
            LeadWorkItem.organization_id == org_uuid,
        ).first()

        if not job or not work_item:
            logger.error(f"Job {job_id} or work item {work_item_id} not found")
            return

        # Step 1: Mark as processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        work_item.status = WorkItemStatus.PROCESSING
        db.add(AuditLog(
            organization_id=org_uuid,
            work_item_id=item_uuid,
            action=AuditAction.JOB_STARTED,
            metadata_json={"job_id": str(job.id), "job_type": job.job_type},
        ))
        db.commit()

        logger.info(f"Processing work item {work_item_id}")

        # Step 2: Simulate email sending (real delay)
        time.sleep(settings.JOB_PROCESSING_DELAY_SECONDS)

        # Simulate occasional failures (10% chance in dev)
        if settings.ENVIRONMENT == "development" and random.random() < 0.1:
            raise Exception("Simulated email delivery failure")

        # Step 3: Simulate CRM sync
        time.sleep(1)
        crm_record_id = f"CRM-{uuid.uuid4().hex[:8].upper()}"

        # Step 4: Mark as completed
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        work_item.status = WorkItemStatus.SENT
        work_item.updated_at = datetime.now(timezone.utc)

        # Create audit log for completion
        email_content = work_item.edited_output or work_item.ai_output
        db.add(AuditLog(
            organization_id=org_uuid,
            work_item_id=item_uuid,
            action=AuditAction.JOB_COMPLETED,
            metadata_json={
                "job_id": str(job.id),
                "crm_record_id": crm_record_id,
                "email_length": len(email_content) if email_content else 0,
                "recipient": work_item.lead_name,
                "company": work_item.company_name,
            },
        ))
        db.commit()

        logger.info(
            f"Work item {work_item_id} processed successfully. "
            f"CRM record: {crm_record_id}"
        )

    except Exception as exc:
        db.rollback()
        logger.error(f"Error processing work item {work_item_id}: {exc}")

        # Update to failed status
        try:
            job = db.query(BackgroundJob).filter(BackgroundJob.id == uuid.UUID(job_id)).first()
            work_item = db.query(LeadWorkItem).filter(LeadWorkItem.id == uuid.UUID(work_item_id)).first()

            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)

            if work_item:
                work_item.status = WorkItemStatus.FAILED
                work_item.updated_at = datetime.now(timezone.utc)

            db.add(AuditLog(
                organization_id=uuid.UUID(organization_id),
                work_item_id=uuid.UUID(work_item_id),
                action=AuditAction.JOB_FAILED,
                metadata_json={
                    "job_id": job_id,
                    "error": str(exc),
                },
            ))
            db.commit()
        except Exception as inner_exc:
            logger.error(f"Failed to update failure status: {inner_exc}")
            db.rollback()

        # Retry if applicable
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

    finally:
        db.close()
