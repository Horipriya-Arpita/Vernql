"""
Schema Service
Handles schema parsing and storage
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog

from app.services.schema_parser import SchemaInfo
from app.services.postgres_parser import PostgreSQLParser
from app.services.mysql_parser import MySQLParser
from app.services.sql_ddl_parser import parse_sql_ddl
from app.services.prisma_parser import parse_prisma_schema
from app.models import (
    Schema,
    SchemaTable,
    SchemaColumn,
    DatabaseType
)

logger = structlog.get_logger()


class SchemaService:
    """Service for parsing and storing database schemas"""

    @staticmethod
    def get_parser(connection_string: str):
        """
        Get appropriate parser for connection string

        Args:
            connection_string: Database connection URL

        Returns:
            SchemaParser instance

        Raises:
            ValueError: If database type is not supported
        """
        conn_lower = connection_string.lower()

        if conn_lower.startswith('postgresql://') or conn_lower.startswith('postgres://'):
            return PostgreSQLParser(connection_string)
        elif conn_lower.startswith('mysql://'):
            return MySQLParser(connection_string)
        else:
            raise ValueError(
                "Unsupported database type. Use postgresql:// or mysql://"
            )

    @staticmethod
    async def parse_and_store_schema(
        db: Session,
        company_id: str,
        schema_name: str,
        connection_string: str,
        include_sample_data: bool = True
    ) -> Schema:
        """
        Parse database schema and store it

        Args:
            db: Database session
            company_id: UUID of the company
            schema_name: Name for this schema
            connection_string: Database connection URL
            include_sample_data: Whether to include sample data

        Returns:
            Schema: The created schema object

        Raises:
            ConnectionError: If unable to connect to target database
            ValueError: If database type not supported
        """
        logger.info(
            "Starting schema parsing",
            company_id=company_id,
            schema_name=schema_name
        )

        # Get appropriate parser
        parser = SchemaService.get_parser(connection_string)

        # Parse the schema
        schema_info: SchemaInfo = await parser.parse_schema(
            include_sample_data=include_sample_data
        )

        logger.info(
            "Schema parsed successfully",
            tables=len(schema_info.tables),
            database_type=schema_info.database_type
        )

        # Store in database
        schema = SchemaService._store_schema(
            db=db,
            company_id=company_id,
            schema_name=schema_name,
            schema_info=schema_info
        )

        logger.info(
            "Schema stored successfully",
            schema_id=str(schema.id),
            tables=len(schema.tables)
        )

        return schema

    @staticmethod
    async def parse_sql_ddl_and_store(
        db: Session,
        company_id: str,
        schema_name: str,
        db_type: str,
        sql_ddl: str
    ) -> Schema:
        """
        Parse SQL DDL and store schema (privacy-first approach)

        This method NEVER accesses customer databases. It only parses SQL DDL text.

        Args:
            db: Database session
            company_id: UUID of the company
            schema_name: Name for this schema
            db_type: Database type ('postgresql' or 'mysql')
            sql_ddl: SQL DDL statements (CREATE TABLE, etc.)

        Returns:
            Schema: The created schema object

        Raises:
            ValueError: If SQL parsing fails
        """
        logger.info(
            "Starting SQL DDL parsing (privacy-first mode)",
            company_id=company_id,
            schema_name=schema_name,
            db_type=db_type,
            ddl_length=len(sql_ddl)
        )

        # Parse SQL DDL to extract schema structure
        schema_info: SchemaInfo = parse_sql_ddl(sql_ddl, db_type)

        logger.info(
            "SQL DDL parsed successfully",
            tables=len(schema_info.tables),
            database_type=schema_info.database_type
        )

        # Store in database, preserving the original DDL text verbatim
        schema = SchemaService._store_schema(
            db=db,
            company_id=company_id,
            schema_name=schema_name,
            schema_info=schema_info,
            raw_ddl_text=sql_ddl,
            schema_format="sql_ddl"
        )

        logger.info(
            "Schema stored successfully (from DDL)",
            schema_id=str(schema.id),
            tables=len(schema.tables)
        )

        return schema

    @staticmethod
    async def parse_prisma_and_store(
        db: Session,
        company_id: str,
        schema_name: str,
        prisma_schema: str,
        db_type_override: Optional[str] = None,
    ) -> Schema:
        """
        Parse a Prisma schema file and store the extracted structure.

        The db_type is read from the datasource block inside the Prisma file.
        db_type_override forces a specific type when the block is absent.

        Args:
            db: Database session
            company_id: UUID of the company
            schema_name: Friendly name for this schema
            prisma_schema: Raw .prisma file text
            db_type_override: Optional 'postgresql' | 'mysql' fallback

        Returns:
            Schema: The created schema object
        """
        logger.info(
            "Starting Prisma schema parsing",
            company_id=company_id,
            schema_name=schema_name,
            schema_length=len(prisma_schema),
        )

        schema_info: SchemaInfo = parse_prisma_schema(prisma_schema, db_type_override)

        if not schema_info.tables:
            raise ValueError(
                "No models were found in the Prisma schema. "
                "Make sure the file contains at least one 'model' block."
            )

        logger.info(
            "Prisma schema parsed successfully",
            tables=len(schema_info.tables),
            database_type=schema_info.database_type,
        )

        schema = SchemaService._store_schema(
            db=db,
            company_id=company_id,
            schema_name=schema_name,
            schema_info=schema_info,
            raw_ddl_text=prisma_schema,
            schema_format="prisma",
        )

        logger.info(
            "Schema stored successfully (from Prisma)",
            schema_id=str(schema.id),
            tables=len(schema.tables),
        )

        return schema

    @staticmethod
    def _store_schema(
        db: Session,
        company_id: str,
        schema_name: str,
        schema_info: SchemaInfo,
        raw_ddl_text: Optional[str] = None,
        schema_format: Optional[str] = None
    ) -> Schema:
        """
        Store parsed schema in database

        Args:
            db: Database session
            company_id: UUID of the company
            schema_name: Name for this schema
            schema_info: Parsed schema information

        Returns:
            Schema: The created schema object
        """
        # Determine database type
        db_type = (
            DatabaseType.POSTGRESQL
            if schema_info.database_type == "postgresql"
            else DatabaseType.MYSQL
        )

        # Create schema object
        schema = Schema(
            company_id=company_id,
            name=schema_name,
            db_type=db_type,
            is_active=True,
            raw_schema={
                "database_name": schema_info.database_name,
                "version": schema_info.version,
                "table_count": len(schema_info.tables)
            },
            raw_ddl_text=raw_ddl_text,
            schema_format=schema_format
        )

        db.add(schema)
        db.flush()  # Get schema ID

        # Create tables and columns
        for table_info in schema_info.tables:
            # Create table
            schema_table = SchemaTable(
                schema_id=schema.id,
                name=table_info.name,
                sample_values={
                    "sample_rows": table_info.sample_data or [],
                    "row_count": table_info.row_count
                }
            )

            db.add(schema_table)
            db.flush()  # Get table ID

            # Create columns
            for col_info in table_info.columns:
                schema_column = SchemaColumn(
                    table_id=schema_table.id,
                    name=col_info.name,
                    data_type=col_info.data_type,
                    is_nullable=col_info.is_nullable,
                    is_primary_key=col_info.is_primary_key,
                    is_foreign_key=col_info.is_foreign_key,
                    is_unique=col_info.is_unique,
                    foreign_key_table=col_info.foreign_key_table,
                    foreign_key_column=col_info.foreign_key_column
                )

                db.add(schema_column)

        # Commit all changes
        db.commit()
        db.refresh(schema)

        return schema

    @staticmethod
    def get_schema_by_id(
        db: Session,
        schema_id: str,
        company_id: str
    ) -> Optional[Schema]:
        """
        Get a schema by ID (with company authorization)

        Args:
            db: Database session
            schema_id: UUID of the schema
            company_id: UUID of the company (for authorization)

        Returns:
            Schema or None if not found/unauthorized
        """
        return db.query(Schema).filter(
            Schema.id == schema_id,
            Schema.company_id == company_id
        ).first()

    @staticmethod
    def list_schemas(
        db: Session,
        company_id: str,
        active_only: bool = True
    ) -> list[Schema]:
        """
        List all schemas for a company

        Args:
            db: Database session
            company_id: UUID of the company
            active_only: Only return active schemas

        Returns:
            List of schemas
        """
        query = db.query(Schema).filter(Schema.company_id == company_id)

        if active_only:
            query = query.filter(Schema.is_active == True)

        return query.order_by(Schema.created_at.desc()).all()

    @staticmethod
    def delete_schema(
        db: Session,
        schema_id: str,
        company_id: str
    ) -> bool:
        """
        Soft delete a schema (mark as inactive)

        Args:
            db: Database session
            schema_id: UUID of the schema
            company_id: UUID of the company (for authorization)

        Returns:
            True if deleted, False if not found
        """
        schema = SchemaService.get_schema_by_id(db, schema_id, company_id)

        if not schema:
            return False

        schema.is_active = False
        db.commit()

        return True
