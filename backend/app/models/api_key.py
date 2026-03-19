"""
API Key Model
Handles authentication and rate limiting for API access
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class APIKey(Base):
    """
    API Key entity for authentication
    Stores hashed API keys with rate limiting configuration
    """
    __tablename__ = "api_keys"

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
        nullable=False,
        index=True
    )

    # API Key Data
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=True)  # Optional friendly name

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Rate Limiting (override company defaults)
    rate_limit_per_minute = Column(Integer, nullable=True)  # None = use company default
    rate_limit_per_hour = Column(Integer, nullable=True)    # None = use company default

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True  # None = never expires
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    company = relationship("Company", back_populates="api_keys")

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_api_keys_company_active', 'company_id', 'is_active'),
    )

    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, company_id={self.company_id})>"

    def is_expired(self) -> bool:
        """Check if API key has expired"""
        if self.expires_at is None:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
