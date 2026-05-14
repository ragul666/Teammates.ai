"""Work Items endpoints — the core sales workflow API."""

import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession
from app.schemas.work_item import (
    WorkItemResponse,
    WorkItemListResponse,
    WorkItemUpdateRequest,
    WorkItemApproveRequest,
    WorkItemRejectRequest,
)
from app.services.work_item_service import WorkItemService
from app.models.work_item import WorkItemStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=WorkItemListResponse)
async def list_work_items(
    current_user: CurrentUser,
    db: DbSession,
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get a paginated list of work items.

    - Admins see all items in their organization
    - Reviewers see only their assigned items
    """
    service = WorkItemService(db)
    return await service.get_work_items(
        user=current_user,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{item_id}", response_model=WorkItemResponse)
async def get_work_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a single work item by ID."""
    service = WorkItemService(db)
    return await service.get_work_item(item_id, current_user)


@router.put("/{item_id}", response_model=WorkItemResponse)
async def update_work_item_draft(
    item_id: uuid.UUID,
    body: WorkItemUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update the draft content of a work item."""
    service = WorkItemService(db)
    return await service.update_draft(item_id, current_user, body.edited_output)


@router.post("/{item_id}/approve", response_model=WorkItemResponse)
async def approve_work_item(
    item_id: uuid.UUID,
    body: WorkItemApproveRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Approve a work item and trigger background processing.

    Prevents duplicate approvals via status guard.
    """
    service = WorkItemService(db)
    return await service.approve_work_item(
        item_id, current_user, body.note, body.edited_output
    )


@router.post("/{item_id}/reject", response_model=WorkItemResponse)
async def reject_work_item(
    item_id: uuid.UUID,
    body: WorkItemRejectRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Reject a work item."""
    service = WorkItemService(db)
    return await service.reject_work_item(item_id, current_user, body.note)


@router.post("/{item_id}/regenerate", response_model=WorkItemResponse)
@limiter.limit("10/minute")
async def regenerate_work_item_draft(
    request: Request,
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Regenerate the AI draft for a work item.

    Rate-limited to prevent LLM abuse.
    """
    service = WorkItemService(db)
    return await service.regenerate_draft(item_id, current_user)


@router.post("/{item_id}/retry", response_model=WorkItemResponse)
async def retry_failed_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Retry a failed work item."""
    service = WorkItemService(db)
    return await service.retry_failed_item(item_id, current_user)


@router.get("/{item_id}/events")
async def work_item_events(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Server-Sent Events endpoint for real-time status updates.

    The frontend connects here after approving an item to receive
    live status updates as the background job progresses.
    """
    # Verify access
    service = WorkItemService(db)
    await service.get_work_item(item_id, current_user)

    async def event_generator():
        """Stream status updates until final state is reached."""
        from app.repositories.work_item_repo import WorkItemRepository
        from app.db.session import async_session_factory

        max_iterations = 60  # Max 60 seconds
        last_status = None

        for _ in range(max_iterations):
            async with async_session_factory() as session:
                repo = WorkItemRepository(session)
                item = await repo.get_by_id(item_id, current_user.organization_id)

                if item and str(item.status.value) != last_status:
                    last_status = str(item.status.value)
                    data = json.dumps({
                        "status": last_status,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                    })
                    yield f"data: {data}\n\n"

                    # Stop streaming on final states
                    if item.status in (
                        WorkItemStatus.SENT,
                        WorkItemStatus.FAILED,
                        WorkItemStatus.REJECTED,
                    ):
                        break

            await asyncio.sleep(1)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
