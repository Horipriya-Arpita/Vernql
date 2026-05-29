"""
Schema Models
Represents database schemas, tables, and columns with AI enrichment
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


class DatabaseType(str, enum.Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class EnrichmentStatus(str, enum.Enum):
    """Lifecycle of AI schema enrichment"""
    PENDING  = "pending"
    RUNNING  = "running"
    COMPLETE = "complete"
    FAILED   = "failed"


class DescriptionSource(str, enum.Enum):
    """Who authored an enriched description"""
    AI   = "ai"
    USER = "user"


class Schema(Base):
    """
    Database Schema entity
    Stores the complete database schema with AI-enriched descriptions
    """
    __tablename__ = "schemas"

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

    # Basic Info
    name = Column(String(255), nullable=False)
    db_type = Column(
        Enum(DatabaseType, native_enum=False),
        nullable=False,
        default=DatabaseType.POSTGRESQL
    )

    # AI Enrichment
    enriched_description = Column(Text, nullable=True)  # AI-generated schema overview
    description_source = Column(String(10), nullable=True)  # 'ai' | 'user' | null

    # Raw Schema Storage (for caching and reference)
    raw_schema = Column(JSONB, nullable=True)  # Parsed schema metadata (table count, db name, etc.)

    # Raw DDL / source text storage
    raw_ddl_text = Column(Text, nullable=True)  # Original input text verbatim (SQL DDL, Prisma, etc.)
    schema_format = Column(String(50), nullable=True)  # Format of the uploaded source: 'sql_ddl' | 'prisma'

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
    enriched_at = Column(
        DateTime(timezone=True),
        nullable=True  # When AI enrichment was last performed
    )
    enrichment_status = Column(
        String(20),
        nullable=False,
        default='pending',
        server_default='pending'
        # 'pending' | 'running' | 'complete' | 'failed'
    )
    enrichment_error = Column(Text, nullable=True)  # Error message when status = 'failed'

    # Relationships
    company = relationship("Company", back_populates="schemas")
    tables = relationship(
        "SchemaTable",
        back_populates="schema",
        cascade="all, delete-orphan"
    )
    queries = relationship(
        "Query",
        back_populates="schema",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session",
        back_populates="schema"
    )

    # Composite indexes
    __table_args__ = (
        Index('ix_schemas_company_active', 'company_id', 'is_active'),
        Index('ix_schemas_company_name', 'company_id', 'name'),
    )

    def __repr__(self):
        return f"<Schema(id={self.id}, name={self.name}, db_type={self.db_type})>"


class SchemaTable(Base):
    """
    Database Table entity
    Represents individual tables within a schema
    """
    __tablename__ = "schema_tables"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Foreign Keys
    schema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schemas.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic Info
    name = Column(String(255), nullable=False)

    # AI Enrichment
    enriched_description = Column(Text, nullable=True)  # AI-generated table description
    description_source = Column(String(10), nullable=True)  # 'ai' | 'user' | null

    # Sample Data (for context in AI prompts)
    sample_values = Column(JSONB, nullable=True)  # Sample rows for better SQL generation

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
    schema = relationship("Schema", back_populates="tables")
    columns = relationship(
        "SchemaColumn",
        back_populates="table",
        cascade="all, delete-orphan"
    )

    # Composite indexes
    __table_args__ = (
        Index('ix_schema_tables_schema_name', 'schema_id', 'name'),
    )

    def __repr__(self):
        return f"<SchemaTable(id={self.id}, name={self.name})>"


class SchemaColumn(Base):
    """
    Database Column entity
    Represents individual columns within a table
    """
    __tablename__ = "schema_columns"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Foreign Keys
    table_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schema_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic Info
    name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)

    # Column Properties
    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_foreign_key = Column(Boolean, default=False, nullable=False)
    is_unique = Column(Boolean, default=False, nullable=False)
    foreign_key_table = Column(String(255), nullable=True)
    foreign_key_column = Column(String(255), nullable=True)

    # AI Enrichment
    enriched_description = Column(Text, nullable=True)  # AI-generated column description
    description_source = Column(String(10), nullable=True)  # 'ai' | 'user' | null

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
    table = relationship("SchemaTable", back_populates="columns")

    # Composite indexes
    __table_args__ = (
        Index('ix_schema_columns_table_name', 'table_id', 'name'),
    )

    def __repr__(self):
        return f"<SchemaColumn(id={self.id}, name={self.name}, type={self.data_type})>"
