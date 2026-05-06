"""
Query Model
Stores query history and analytics
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum


from app.db.database import Base


class QueryStatus(str, enum.Enum):
    """Query execution status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class Query(Base):
    """
    Query History entity
    Stores all natural language queries and generated SQL with analytics
    """
    __tablename__ = "queries"

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
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schemas.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True
    )
    turn_number = Column(
        Integer,
        nullable=True,
        comment="Position of this query within its session (1-based)"
    )

    # Query Data
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)

    # AI Metadata
    ai_provider = Column(String(50), nullable=True)  # openai, anthropic, etc.
    ai_model = Column(String(100), nullable=True)    # gpt-4, claude-3, etc.
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0

    # Execution Results
    status = Column(
        Enum(QueryStatus, native_enum=False),
        nullable=False,
        default=QueryStatus.SUCCESS
    )
    execution_time_ms = Column(Integer, nullable=True)
    result_count = Column(Integer, nullable=True)  # Number of rows returned
    error_message = Column(Text, nullable=True)

    # Additional Metadata
    query_metadata = Column(JSONB, nullable=True)  # Additional context, user info, etc.

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    company = relationship("Company", back_populates="queries")
    schema = relationship("Schema", back_populates="queries")
    session = relationship("Session", back_populates="queries")
    results = relationship("QueryResult", back_populates="query", cascade="all, delete-orphan")

    # Composite indexes for analytics
    __table_args__ = (
        Index('ix_queries_company_created', 'company_id', 'created_at'),
        Index('ix_queries_schema_created', 'schema_id', 'created_at'),
        Index('ix_queries_status', 'status'),
        Index('ix_queries_session_turn', 'session_id', 'turn_number'),
    )

    def __repr__(self):
        return f"<Query(id={self.id}, status={self.status}, created_at={self.created_at})>"
