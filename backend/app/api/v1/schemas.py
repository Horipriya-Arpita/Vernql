"""
Schema Management Endpoints
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import CurrentCompany
from app.services.schema_service import SchemaService
from app.services.enrichment_service import EnrichmentService
from app.models import Schema

router = APIRouter(prefix="/schemas", tags=["Schemas"])


# Pydantic schemas
class SchemaUploadRequest(BaseModel):
    """Request schema for uploading/parsing a database schema"""
    name: str = Field(..., description="Name for this schema", max_length=255)
    connection_string: str = Field(
        ...,
        description="Database connection string (postgresql:// or mysql://)"
    )
    include_sample_data: bool = Field(
        True,
        description="Whether to include sample data from tables"
    )


class ColumnResponse(BaseModel):
    """Response schema for a column"""
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: Optional[str]
    foreign_key_column: Optional[str]
    enriched_description: Optional[str]

    class Config:
        from_attributes = True


class TableResponse(BaseModel):
    """Response schema for a table"""
    id: UUID
    name: str
    enriched_description: Optional[str]
    columns: List[ColumnResponse]

    class Config:
        from_attributes = True


class SchemaResponse(BaseModel):
    """Response schema for a complete schema"""
    id: UUID
    name: str
    db_type: str
    is_active: bool
    created_at: str
    enriched_description: Optional[str]
    table_count: int

    class Config:
        from_attributes = True


class SchemaDetailResponse(SchemaResponse):
    """Detailed response with tables and columns"""
    tables: List[TableResponse]


class SchemaListResponse(BaseModel):
    """Response for list of schemas"""
    schemas: List[SchemaResponse]
    total: int


@router.post(
    "",
    response_model=SchemaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a database schema"
)
async def upload_schema(
    schema_data: SchemaUploadRequest,
    company: CurrentCompany,
    db: Session = Depends(get_db)
):
    """
    Upload and parse a database schema

    Connects to the specified database and extracts its complete schema
    including tables, columns, relationships, and optionally sample data.

    **Supported databases:**
    - PostgreSQL (postgresql://...)
    - MySQL (mysql://...)

    **Connection string format:**
    - PostgreSQL: `postgresql://user:password@host:port/database`
    - MySQL: `mysql://user:password@host:port/database`

    **Security:**
    - Connection strings are not stored
    - Only schema metadata is stored
    - Credentials are used only during parsing

    ## Parameters
    - **name**: Friendly name for this schema
    - **connection_string**: Database connection URL
    - **include_sample_data**: Include sample rows for AI context (default: true)

    ## Response
    Returns the created schema with metadata
    """
    try:
        # Parse and store schema
        schema = await SchemaService.parse_and_store_schema(
            db=db,
            company_id=str(company.id),
            schema_name=schema_data.name,
            connection_string=schema_data.connection_string,
            include_sample_data=schema_data.include_sample_data
        )

        return SchemaResponse(
            id=schema.id,
            name=schema.name,
            db_type=schema.db_type.value,
            is_active=schema.is_active,
            created_at=schema.created_at.isoformat(),
            enriched_description=schema.enriched_description,
            table_count=len(schema.tables)
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to database: {str(e)}"
        )
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
    company: CurrentCompany,
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
            table_count=len(s.tables)
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
    company: CurrentCompany,
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
        table_count=len(schema.tables),
        tables=tables_response
    )


@router.delete(
    "/{schema_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a schema"
)
async def delete_schema(
    schema_id: UUID,
    company: CurrentCompany,
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


@router.post(
    "/{schema_id}/enrich",
    response_model=SchemaResponse,
    summary="Enrich schema with AI descriptions"
)
async def enrich_schema(
    schema_id: UUID,
    company: CurrentCompany,
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
            table_count=len(enriched_schema.tables)
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
