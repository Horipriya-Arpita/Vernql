"""
Schema Management Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.core.dependencies import CurrentCompany, CurrentCompanyEither
from app.services.schema_service import SchemaService
from app.services.enrichment_service import EnrichmentService
from app.models import Schema, SchemaTable, SchemaColumn

router = APIRouter(prefix="/schemas", tags=["Schemas"])

_log = __import__("structlog").get_logger()


async def _enrich_in_background(schema_id: str) -> None:
    """
    Background task: enrich a schema with AI descriptions using its own DB session.

    Runs after the upload response is already sent so the user is never blocked.
    Sets enrichment_status to 'running' → 'complete' or 'failed' so the UI
    can surface the result instead of spinning indefinitely.
    """
    db = SessionLocal()
    try:
        # Mark as running so the UI knows enrichment has started
        schema = db.query(Schema).filter(Schema.id == schema_id).first()
        if schema:
            schema.enrichment_status = 'running'
            schema.enrichment_error = None
            db.commit()

        enrichment_service = EnrichmentService()
        await enrichment_service.enrich_schema(db=db, schema_id=schema_id)

        # Mark complete (enrichment_service already committed enriched_at)
        schema = db.query(Schema).filter(Schema.id == schema_id).first()
        if schema:
            schema.enrichment_status = 'complete'
            db.commit()

        _log.info("Background enrichment complete", schema_id=schema_id)
    except Exception as exc:
        _log.error("Background enrichment failed", schema_id=schema_id, error=str(exc))
        try:
            schema = db.query(Schema).filter(Schema.id == schema_id).first()
            if schema:
                schema.enrichment_status = 'failed'
                schema.enrichment_error = str(exc)[:500]
                db.commit()
        except Exception:
            pass  # Don't let error-handling itself blow up
    finally:
        db.close()


# Pydantic schemas
class SchemaUploadRequest(BaseModel):
    """Request schema for uploading/parsing a database schema"""
    name: str = Field(..., description="Name for this schema", max_length=255)
    schema_format: str = Field(
        default="sql_ddl",
        description="Format of the uploaded schema: 'sql_ddl' or 'prisma'",
        pattern="^(sql_ddl|prisma)$"
    )
    db_type: Optional[str] = Field(
        default=None,
        description=(
            "Database type (postgresql or mysql). "
            "Required for sql_ddl format. "
            "Optional for prisma format — extracted from the datasource block."
        ),
    )
    sql_ddl: str = Field(
        ...,
        description=(
            "Schema content. For sql_ddl: CREATE TABLE statements from pg_dump/mysqldump. "
            "For prisma: raw content of a .prisma file."
        ),
        min_length=1
    )


class ColumnResponse(BaseModel):
    """Response schema for a column"""
    id: UUID
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: Optional[str] = None
    foreign_key_column: Optional[str] = None
    enriched_description: Optional[str] = None
    description_source: Optional[str] = None  # 'ai' | 'user' | null

    class Config:
        from_attributes = True


class TableResponse(BaseModel):
    """Response schema for a table"""
    id: UUID
    name: str
    enriched_description: Optional[str] = None
    description_source: Optional[str] = None  # 'ai' | 'user' | null
    columns: List[ColumnResponse]

    class Config:
        from_attributes = True


class DescriptionUpdateRequest(BaseModel):
    """Request body for updating a single enriched description"""
    enriched_description: str = Field(..., min_length=1, max_length=2000)


class SchemaResponse(BaseModel):
    """Response schema for a complete schema"""
    id: UUID
    name: str
    db_type: str
    is_active: bool
    created_at: str
    enriched_description: Optional[str]
    table_count: int
    enriched_at: Optional[str] = None
    enrichment_status: str = 'pending'   # 'pending' | 'running' | 'complete' | 'failed'
    enrichment_error: Optional[str] = None

    class Config:
        from_attributes = True


class SchemaDetailResponse(SchemaResponse):
    """Detailed response with tables and columns"""
    tables: List[TableResponse]
    raw_ddl_text: Optional[str] = None  # Original uploaded DDL/schema text
    schema_format: Optional[str] = None  # Source format: 'sql_ddl' | 'prisma'


class SchemaListResponse(BaseModel):
    """Response for list of schemas"""
    schemas: List[SchemaResponse]
    total: int


@router.post(
    "",
    response_model=SchemaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a database schema from SQL DDL"
)
async def upload_schema(
    schema_data: SchemaUploadRequest,
    background_tasks: BackgroundTasks,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """
    Upload and parse a database schema from SQL DDL statements

    **Privacy-First Design:**
    - You NEVER provide database credentials
    - You ONLY upload SQL DDL (schema structure)
    - We NEVER access your database directly
    - We NEVER store your actual data

    **How to export your schema:**
    - PostgreSQL: `pg_dump --schema-only your_database > schema.sql`
    - MySQL: `mysqldump --no-data your_database > schema.sql`

    **Supported databases:**
    - PostgreSQL
    - MySQL

    ## Parameters
    - **name**: Friendly name for this schema
    - **db_type**: Database type (postgresql or mysql)
    - **sql_ddl**: SQL DDL statements (CREATE TABLE, ALTER TABLE, etc.)

    ## Response
    Returns the created schema with metadata

    ## Example
    ```json
    {
      "name": "E-commerce Database",
      "db_type": "postgresql",
      "sql_ddl": "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255));"
    }
    ```
    """
    try:
        fmt = schema_data.schema_format

        if fmt == "prisma":
            schema = await SchemaService.parse_prisma_and_store(
                db=db,
                company_id=str(company.id),
                schema_name=schema_data.name,
                prisma_schema=schema_data.sql_ddl,
                db_type_override=schema_data.db_type,
            )

        else:  # sql_ddl (default)
            if not schema_data.db_type:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="db_type is required when schema_format is 'sql_ddl'. Use 'postgresql' or 'mysql'.",
                )
            if schema_data.db_type not in ("postgresql", "mysql"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="db_type must be 'postgresql' or 'mysql'.",
                )
            schema = await SchemaService.parse_sql_ddl_and_store(
                db=db,
                company_id=str(company.id),
                schema_name=schema_data.name,
                db_type=schema_data.db_type,
                sql_ddl=schema_data.sql_ddl,
            )

        # Schedule AI enrichment in the background so the response is instant.
        # The task creates its own DB session; failures are silent to the caller.
        background_tasks.add_task(_enrich_in_background, str(schema.id))

        return SchemaResponse(
            id=schema.id,
            name=schema.name,
            db_type=schema.db_type.value,
            is_active=schema.is_active,
            created_at=schema.created_at.isoformat(),
            enriched_description=schema.enriched_description,
            enriched_at=schema.enriched_at.isoformat() if schema.enriched_at else None,
            table_count=len(schema.tables),
            enrichment_status=schema.enrichment_status or 'pending',
            enrichment_error=schema.enrichment_error,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse schema: {str(e)}"
        )


@router.get(
    "",
    response_model=SchemaListResponse,
    summary="List all schemas"
)
async def list_schemas(
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
    active_only: bool = True
):
    """
    List all schemas for the authenticated company

    ## Parameters
    - **active_only**: Only return active schemas (default: true)

    ## Response
    Returns list of schemas with basic metadata
    """
    schemas = SchemaService.list_schemas(
        db=db,
        company_id=str(company.id),
        active_only=active_only
    )

    schema_responses = [
        SchemaResponse(
            id=s.id,
            name=s.name,
            db_type=s.db_type.value,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
            enriched_description=s.enriched_description,
            enriched_at=s.enriched_at.isoformat() if s.enriched_at else None,
            table_count=len(s.tables),
            enrichment_status=s.enrichment_status or 'pending',
            enrichment_error=s.enrichment_error,
        )
        for s in schemas
    ]

    return SchemaListResponse(
        schemas=schema_responses,
        total=len(schema_responses)
    )


@router.get(
    "/{schema_id}",
    response_model=SchemaDetailResponse,
    summary="Get schema details"
)
async def get_schema(
    schema_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific schema

    Includes all tables and columns with their metadata

    ## Parameters
    - **schema_id**: UUID of the schema

    ## Response
    Returns complete schema with tables and columns
    """
    schema = SchemaService.get_schema_by_id(
        db=db,
        schema_id=str(schema_id),
        company_id=str(company.id)
    )

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found"
        )

    # Build response with tables and columns
    tables_response = []
    for table in schema.tables:
        columns_response = [
            ColumnResponse.from_orm(col)
            for col in table.columns
        ]

        tables_response.append(
            TableResponse(
                id=table.id,
                name=table.name,
                enriched_description=table.enriched_description,
                description_source=table.description_source,
                columns=columns_response
            )
        )

    return SchemaDetailResponse(
        id=schema.id,
        name=schema.name,
        db_type=schema.db_type.value,
        is_active=schema.is_active,
        created_at=schema.created_at.isoformat(),
        enriched_description=schema.enriched_description,
        enriched_at=schema.enriched_at.isoformat() if schema.enriched_at else None,
        table_count=len(schema.tables),
        tables=tables_response,
        raw_ddl_text=schema.raw_ddl_text,
        schema_format=schema.schema_format,
        enrichment_status=schema.enrichment_status or 'pending',
        enrichment_error=schema.enrichment_error,
    )


@router.delete(
    "/{schema_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a schema"
)
async def delete_schema(
    schema_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a schema

    This marks the schema as inactive but doesn't delete it from the database.
    Queries using this schema will no longer work.

    ## Parameters
    - **schema_id**: UUID of the schema to delete

    ## Response
    Returns 204 No Content on success
    """
    deleted = SchemaService.delete_schema(
        db=db,
        schema_id=str(schema_id),
        company_id=str(company.id)
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found"
        )

    return None


@router.patch(
    "/{schema_id}",
    response_model=SchemaResponse,
    summary="Update the schema-level description"
)
async def update_schema_description(
    schema_id: UUID,
    body: DescriptionUpdateRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """
    Manually set or edit the schema-level description.
    Marks description_source as 'user' so re-enrichment won't overwrite it.
    """
    schema = SchemaService.get_schema_by_id(db, str(schema_id), str(company.id))
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    schema.enriched_description = body.enriched_description
    schema.description_source = "user"
    db.commit()
    db.refresh(schema)

    return SchemaResponse(
        id=schema.id,
        name=schema.name,
        db_type=schema.db_type.value,
        is_active=schema.is_active,
        created_at=schema.created_at.isoformat(),
        enriched_description=schema.enriched_description,
        enriched_at=schema.enriched_at.isoformat() if schema.enriched_at else None,
        table_count=len(schema.tables),
    )


@router.patch(
    "/{schema_id}/tables/{table_id}",
    response_model=TableResponse,
    summary="Update a table description"
)
async def update_table_description(
    schema_id: UUID,
    table_id: UUID,
    body: DescriptionUpdateRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """
    Manually set or edit a table's enriched description.
    Marks description_source as 'user' so re-enrichment won't overwrite it.
    """
    schema = SchemaService.get_schema_by_id(db, str(schema_id), str(company.id))
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    table = (
        db.query(SchemaTable)
        .filter(SchemaTable.id == table_id, SchemaTable.schema_id == schema_id)
        .first()
    )
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    table.enriched_description = body.enriched_description
    table.description_source = "user"
    db.commit()
    db.refresh(table)

    return TableResponse(
        id=table.id,
        name=table.name,
        enriched_description=table.enriched_description,
        description_source=table.description_source,
        columns=[ColumnResponse.from_orm(c) for c in table.columns],
    )


@router.patch(
    "/{schema_id}/tables/{table_id}/columns/{column_id}",
    response_model=ColumnResponse,
    summary="Update a column description"
)
async def update_column_description(
    schema_id: UUID,
    table_id: UUID,
    column_id: UUID,
    body: DescriptionUpdateRequest,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db),
):
    """
    Manually set or edit a column's enriched description.
    Marks description_source as 'user' so re-enrichment won't overwrite it.
    """
    schema = SchemaService.get_schema_by_id(db, str(schema_id), str(company.id))
    if not schema:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schema not found")

    table = (
        db.query(SchemaTable)
        .filter(SchemaTable.id == table_id, SchemaTable.schema_id == schema_id)
        .first()
    )
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")

    column = (
        db.query(SchemaColumn)
        .filter(SchemaColumn.id == column_id, SchemaColumn.table_id == table_id)
        .first()
    )
    if not column:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")

    column.enriched_description = body.enriched_description
    column.description_source = "user"
    db.commit()
    db.refresh(column)

    return ColumnResponse.from_orm(column)


@router.post(
    "/{schema_id}/enrich",
    response_model=SchemaResponse,
    summary="Enrich schema with AI descriptions"
)
async def enrich_schema(
    schema_id: UUID,
    company: CurrentCompanyEither,
    db: Session = Depends(get_db)
):
    """
    Enrich a schema with AI-generated descriptions

    Uses AI (OpenAI or Anthropic) to generate human-friendly descriptions for:
    - Overall schema purpose
    - Each table's business meaning
    - Each column's data meaning

    This improves SQL generation quality by giving the AI better context about
    the database structure and business domain.

    **Note:** This operation may take 30-60 seconds for large schemas as it
    makes multiple AI API calls.

    ## Parameters
    - **schema_id**: UUID of the schema to enrich

    ## Response
    Returns the enriched schema with generated descriptions
    """
    # Verify schema exists and belongs to company
    schema = SchemaService.get_schema_by_id(
        db=db,
        schema_id=str(schema_id),
        company_id=str(company.id)
    )

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schema not found"
        )

    try:
        # Enrich schema
        enrichment_service = EnrichmentService()
        enriched_schema = await enrichment_service.enrich_schema(
            db=db,
            schema_id=str(schema_id)
        )

        return SchemaResponse(
            id=enriched_schema.id,
            name=enriched_schema.name,
            db_type=enriched_schema.db_type.value,
            is_active=enriched_schema.is_active,
            created_at=enriched_schema.created_at.isoformat(),
            enriched_description=enriched_schema.enriched_description,
            enriched_at=enriched_schema.enriched_at.isoformat() if enriched_schema.enriched_at else None,
            table_count=len(enriched_schema.tables),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enrich schema: {str(e)}"
        )
