"""
Query Example Model
Stores example queries for few-shot learning and query improvement
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class ExampleSource(str, enum.Enum):
    """Source of the example query"""
    MANUAL = "manual"  # Manually created by user
    AUTO_GENERATED = "auto_generated"  # AI-generated
    USER_FEEDBACK = "user_feedback"  # From successful user queries
    CURATED = "curated"  # Curated by platform


class QueryExample(Base):
    """
    Example queries for few-shot learning

    Stores high-quality example query pairs (natural language -> SQL)
    that can be used to improve SQL generation through few-shot learning
    """
    __tablename__ = "query_examples"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    schema_id = Column(UUID(as_uuid=True), ForeignKey("schemas.id"), nullable=True, index=True)

    # Example content
    natural_language = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    # Metadata
    source = Column(SQLEnum(ExampleSource), nullable=False, default=ExampleSource.MANUAL)
    tags = Column(Text, nullable=True)  # Comma-separated tags (e.g., "aggregation,join,date")
    difficulty = Column(String(20), nullable=True)  # "easy", "medium", "hard"

    # Quality and usage
    quality_score = Column(Integer, nullable=True)  # 1-10 rating
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Integer, nullable=True)  # Percentage of successful uses

    # Active status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", backref="query_examples")
    schema = relationship("Schema", backref="query_examples")

    def __repr__(self):
        return f"<QueryExample {self.id}: {self.natural_language[:50]}...>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "schema_id": str(self.schema_id) if self.schema_id else None,
            "natural_language": self.natural_language,
            "sql_query": self.sql_query,
            "explanation": self.explanation,
            "source": self.source.value,
            "tags": self.tags.split(",") if self.tags else [],
            "difficulty": self.difficulty,
            "quality_score": self.quality_score,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
