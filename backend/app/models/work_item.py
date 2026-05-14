"""Lead Work Item model — core sales workflow entity."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class WorkItemStatus(str, enum.Enum):
    """Status lifecycle for work items."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATING = "regenerating"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"


class LeadWorkItem(Base):
    __tablename__ = "lead_work_items"
    __table_args__ = (
        Index("ix_work_items_organization_id", "organization_id"),
        Index("ix_work_items_status", "status"),
        Index("ix_work_items_assigned_reviewer", "assigned_reviewer_id"),
        Index("ix_work_items_org_status", "organization_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Lead info
    lead_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    lead_context: Mapped[str] = mapped_column(Text, nullable=False)
    original_input: Mapped[str] = mapped_column(Text, nullable=False)

    # AI output
    ai_output: Mapped[str] = mapped_column(Text, nullable=False)
    edited_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[WorkItemStatus] = mapped_column(
        Enum(WorkItemStatus),
        nullable=False,
        default=WorkItemStatus.PENDING_REVIEW,
    )

    # Notes
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    organization = relationship("Organization", back_populates="work_items")
    assigned_reviewer = relationship("User", back_populates="assigned_work_items")
    audit_logs = relationship("AuditLog", back_populates="work_item", lazy="selectin")
    background_jobs = relationship("BackgroundJob", back_populates="work_item", lazy="selectin")

    def __repr__(self) -> str:
        return f"<LeadWorkItem(id={self.id}, lead={self.lead_name}, status={self.status})>"
