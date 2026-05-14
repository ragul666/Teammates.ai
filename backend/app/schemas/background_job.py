"""Background Job schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BackgroundJobResponse(BaseModel):
    """Background job response."""
    id: str
    organization_id: str
    work_item_id: str
    job_type: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
