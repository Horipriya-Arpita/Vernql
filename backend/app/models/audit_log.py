"""
Audit Log Model
Immutable record of every significant action taken in the system.
Used for compliance, debugging, and security reviews.
"""
import enum
import uuid

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.db.database import Base


class AuditAction(str, enum.Enum):
    """Standardised action codes — format: resource.verb"""
    # Queries
    QUERY_GENERATE   = "query.generate"
    # Schemas
    SCHEMA_UPLOAD    = "schema.upload"
    SCHEMA_DELETE    = "schema.delete"
    SCHEMA_ENRICH    = "schema.enrich"
    # API Keys
    API_KEY_CREATE   = "api_key.create"
    API_KEY_REVOKE   = "api_key.revoke"
    # Auth
    USER_LOGIN       = "user.login"
    USER_REGISTER    = "user.register"
    # Results
    RESULT_SHARE     = "result.share"


class AuditLog(Base):
    """
    Immutable audit trail entry.

    Never update or delete rows from this table — its value is that it
    cannot be altered after the fact. Use soft-delete on other tables instead.
    """
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Tenant isolation
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Actor — one of these will be set, never both
    user_id    = Column(UUID(as_uuid=True), nullable=True)   # set on JWT auth
    api_key_id = Column(UUID(as_uuid=True), nullable=True)   # set on API key auth

    # What happened
    action        = Column(String(60),  nullable=False, index=True)  # AuditAction value
    resource_type = Column(String(50),  nullable=True)               # "query", "schema", …
    resource_id   = Column(UUID(as_uuid=True), nullable=True)        # UUID of affected object

    # Optional structured context (confidence score, error message, etc.)
    details = Column(JSONB, nullable=True)

    # Network context
    ip_address = Column(String(45), nullable=True)   # IPv4 or IPv6

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_audit_logs_company_created", "company_id", "created_at"),
        Index("ix_audit_logs_company_action",  "company_id", "action"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, company={self.company_id})>"