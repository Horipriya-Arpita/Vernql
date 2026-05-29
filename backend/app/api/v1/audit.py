"""
Audit Log Endpoints
Read-only access to the company's audit trail.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import CurrentCompanyEither
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogEntry(BaseModel):
    id: UUID
    user_id:       Optional[UUID]
    api_key_id:    Optional[UUID]
    action:        str
    resource_type: Optional[str]
    resource_id:   Optional[UUID]
    details:       Optional[dict]
    ip_address:    Optional[str]
    created_at:    datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    entries: List[AuditLogEntry]
    total:   int


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List audit log entries",
)
async def list_audit_logs(
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
    action:        Optional[str]      = Query(None, description="Filter by action, e.g. query.generate"),
    resource_type: Optional[str]      = Query(None, description="Filter by resource type, e.g. schema"),
    resource_id:   Optional[UUID]     = Query(None, description="Filter by resource UUID"),
    from_date:     Optional[datetime] = Query(None, description="Entries on or after this datetime (ISO-8601)"),
    to_date:       Optional[datetime] = Query(None, description="Entries on or before this datetime (ISO-8601)"),
    limit:         int                = Query(50, ge=1, le=500),
    offset:        int                = Query(0,  ge=0),
):
    """
    Retrieve the audit trail for your company.

    Results are ordered newest-first. Use `from_date` / `to_date` for
    time-range queries and `action` / `resource_type` to narrow results.
    """
    q = db.query(AuditLog).filter(AuditLog.company_id == company.id)

    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        q = q.filter(AuditLog.resource_id == resource_id)
    if from_date:
        q = q.filter(AuditLog.created_at >= from_date)
    if to_date:
        q = q.filter(AuditLog.created_at <= to_date)

    total   = q.count()
    entries = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    return AuditLogListResponse(
        entries=[AuditLogEntry.model_validate(e) for e in entries],
        total=total,
    )