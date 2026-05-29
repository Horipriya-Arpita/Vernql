"""
QueryResult Model
Stores the actual results from executed queries for visualization
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class QueryResult(Base):
    """
    Query Result entity
    Stores executed query results for visualization and sharing
    """
    __tablename__ = "query_results"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Foreign Keys
    query_id = Column(
        UUID(as_uuid=True),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Denormalized session FK — avoids join for get_latest_result"
    )

    # Result Data
    results_data = Column(
        JSON,
        nullable=False,
        comment="Array of result rows returned from query execution"
    )
    row_count = Column(
        Integer,
        nullable=False,
        comment="Number of rows in the result set"
    )
    column_count = Column(
        Integer,
        nullable=False,
        comment="Number of columns in the result set"
    )

    # Visualization
    chart_type = Column(
        String(50),
        nullable=True,
        comment="Auto-detected chart type: metric, bar, line, pie, table"
    )
    ai_insight = Column(
        Text,
        nullable=True,
        comment="AI-generated insight about the data"
    )

    # Sharing
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this visualization is publicly shareable"
    )
    share_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the public share link expires. NULL = never expires.",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    query = relationship("Query", back_populates="results")
    company = relationship("Company", back_populates="query_results")
    session = relationship("Session", back_populates="query_results")

    __table_args__ = (
        Index("ix_query_results_session_created", "session_id", "created_at"),
    )

    def __repr__(self):
        return f"<QueryResult(id={self.id}, query_id={self.query_id}, rows={self.row_count})>"