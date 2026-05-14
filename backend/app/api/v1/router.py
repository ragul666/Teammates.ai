"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.work_items import router as work_items_router
from app.api.v1.audit import router as audit_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(work_items_router, prefix="/work-items", tags=["Work Items"])
api_router.include_router(audit_router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
