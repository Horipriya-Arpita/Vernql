"""
Session Model
Groups multiple queries into a single conversational session
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Session(Base):
    """
    Session entity
    Groups queries into a conversation so multiple NL questions can be asked
    against the same schema without losing context.
    """
    __tablename__ = "sessions"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Foreign Keys
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schemas.id", ondelete="SET NULL"),
        nullable=True  # nullable: schema may change mid-session
    )

    # Session metadata
    title = Column(
        String(80),
        nullable=True,
        comment="Auto-set from the first question, trimmed to 80 chars"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    company = relationship("Company", back_populates="sessions")
    schema = relationship("Schema", back_populates="sessions")
    queries = relationship("Query", back_populates="session")
    query_results = relationship("QueryResult", back_populates="session")

    __table_args__ = (
        Index("ix_sessions_company_created", "company_id", "created_at"),
        Index("ix_sessions_company_active", "company_id", "is_active"),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, company_id={self.company_id}, is_active={self.is_active})>"