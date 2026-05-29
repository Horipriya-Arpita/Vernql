"""
Audit Service
Fire-and-forget helper for writing audit log entries.

Usage (inside a route handler):
    from app.services.audit_service import AuditService, AuditAction

    AuditService.log(
        db=db,
        company_id=company.id,
        action=AuditAction.QUERY_GENERATE,
        resource_type="query",
        resource_id=query_record.id,
        details={"confidence": result.confidence},
        request=request,        # FastAPI Request — extracts IP automatically
    )

Audit entries are committed immediately in their own DB flush so that
a later rollback in the caller does NOT lose the audit record.
"""
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditAction

logger = structlog.get_logger()


class AuditService:

    @staticmethod
    def log(
        db: Session,
        company_id: UUID,
        action: AuditAction,
        *,
        resource_type: Optional[str] = None,
        resource_id:   Optional[UUID] = None,
        details:       Optional[Dict[str, Any]] = None,
        user_id:       Optional[UUID] = None,
        api_key_id:    Optional[UUID] = None,
        ip_address:    Optional[str]  = None,
        request=None,   # FastAPI Request object — extracts IP when provided
    ) -> None:
        """
        Write one audit log entry and commit it immediately.

        Errors are swallowed and logged — audit failures must never break
        the primary request.
        """
        try:
            if ip_address is None and request is not None:
                ip_address = AuditService._extract_ip(request)

            entry = AuditLog(
                company_id    = company_id,
                user_id       = user_id,
                api_key_id    = api_key_id,
                action        = action.value,
                resource_type = resource_type,
                resource_id   = resource_id,
                details       = details,
                ip_address    = ip_address,
            )
            db.add(entry)
            db.commit()

        except Exception as exc:
            logger.error("audit_log_failed", action=action, error=str(exc))
            try:
                db.rollback()
            except Exception:
                pass

    @staticmethod
    def _extract_ip(request) -> Optional[str]:
        """Extract client IP, honouring X-Forwarded-For when behind a proxy."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return None