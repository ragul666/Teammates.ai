"""Audit Log model — tracks all important actions."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Enum, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AuditAction(str, enum.Enum):
    """Types of auditable actions."""
    ITEM_CREATED = "item_created"
    AI_DRAFT_GENERATED = "ai_draft_generated"
    DRAFT_REGENERATED = "draft_regenerated"
    DRAFT_EDITED = "draft_edited"
    ITEM_APPROVED = "item_approved"
    ITEM_REJECTED = "item_rejected"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    USER_LOGIN = "user_login"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_organization_id", "organization_id"),
        Index("ix_audit_logs_work_item_id", "work_item_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lead_work_items.id"), nullable=True
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    work_item = relationship("LeadWorkItem", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_actions")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action})>"
