"""
Company Model
Represents a tenant/organization in the system
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Company(Base):
    """
    Company/Organization entity
    Each company is a separate tenant with isolated data
    """
    __tablename__ = "companies"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Basic Info
    name = Column(String(255), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

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
    users = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "APIKey",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    schemas = relationship(
        "Schema",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    queries = relationship(
        "Query",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    query_results = relationship(
        "QueryResult",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name={self.name})>"
