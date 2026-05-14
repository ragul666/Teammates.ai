"""Work Item schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WorkItemResponse(BaseModel):
    """Full work item response."""
    id: str
    organization_id: str
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    lead_name: str
    company_name: str
    lead_context: str
    original_input: str
    ai_output: str
    edited_output: Optional[str] = None
    status: str
    reviewer_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkItemListResponse(BaseModel):
    """Paginated list of work items."""
    items: list[WorkItemResponse]
    total: int
    page: int
    page_size: int


class WorkItemUpdateRequest(BaseModel):
    """Update a work item draft."""
    edited_output: str = Field(..., min_length=1, max_length=10000)


class WorkItemApproveRequest(BaseModel):
    """Approve a work item."""
    note: Optional[str] = Field(None, max_length=1000)
    edited_output: Optional[str] = Field(None, max_length=10000)


class WorkItemRejectRequest(BaseModel):
    """Reject a work item."""
    note: Optional[str] = Field(None, max_length=1000)


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_items: int
    pending_review: int
    approved: int
    rejected: int
    processing: int
    sent: int
    failed: int
