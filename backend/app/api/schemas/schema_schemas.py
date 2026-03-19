"""
Schema-related Pydantic Models
Request/response models for schema endpoints
"""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SchemaUploadRequest(BaseModel):
    """Request schema for uploading/parsing a database schema"""
    name: str = Field(..., description="Name for this schema", max_length=255, min_length=1)
    connection_string: str = Field(
        ...,
        description="Database connection string (postgresql:// or mysql://)",
        min_length=10
    )
    include_sample_data: bool = Field(
        True,
        description="Whether to include sample data from tables"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production E-commerce DB",
                "connection_string": "postgresql://user:password@localhost:5432/ecommerce",
                "include_sample_data": True
            }
        }


class ColumnResponse(BaseModel):
    """Response schema for a database column"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Column data type")
    is_nullable: bool = Field(..., description="Whether column allows NULL values")
    is_primary_key: bool = Field(..., description="Whether column is a primary key")
    is_foreign_key: bool = Field(..., description="Whether column is a foreign key")
    foreign_key_table: Optional[str] = Field(None, description="Referenced table if foreign key")
    foreign_key_column: Optional[str] = Field(None, description="Referenced column if foreign key")
    enriched_description: Optional[str] = Field(None, description="AI-generated description")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "user_id",
                "data_type": "INTEGER",
                "is_nullable": False,
                "is_primary_key": False,
                "is_foreign_key": True,
                "foreign_key_table": "users",
                "foreign_key_column": "id",
                "enriched_description": "Reference to the user who created this record"
            }
        }


class TableResponse(BaseModel):
    """Response schema for a database table"""
    id: UUID = Field(..., description="Table UUID")
    name: str = Field(..., description="Table name")
    enriched_description: Optional[str] = Field(None, description="AI-generated table description")
    columns: List[ColumnResponse] = Field(..., description="List of columns in this table")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "orders",
                "enriched_description": "Customer order records with status and payment information",
                "columns": []
            }
        }


class SchemaResponse(BaseModel):
    """Response schema for a database schema (summary)"""
    id: UUID = Field(..., description="Schema UUID")
    name: str = Field(..., description="Schema name")
    db_type: str = Field(..., description="Database type (postgresql, mysql, etc.)")
    is_active: bool = Field(..., description="Whether schema is active")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    enriched_description: Optional[str] = Field(None, description="AI-generated schema description")
    table_count: int = Field(..., description="Number of tables in schema")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Production E-commerce DB",
                "db_type": "postgresql",
                "is_active": True,
                "created_at": "2024-03-14T10:30:00Z",
                "enriched_description": "E-commerce platform database containing users, products, orders, and payments",
                "table_count": 15
            }
        }


class SchemaDetailResponse(SchemaResponse):
    """Detailed schema response with all tables and columns"""
    tables: List[TableResponse] = Field(..., description="Complete list of tables with columns")

    class Config:
        from_attributes = True


class SchemaListResponse(BaseModel):
    """Response for list of schemas"""
    schemas: List[SchemaResponse] = Field(..., description="List of schemas")
    total: int = Field(..., description="Total number of schemas")

    class Config:
        json_schema_extra = {
            "example": {
                "schemas": [],
                "total": 0
            }
        }


class SchemaUpdateRequest(BaseModel):
    """Request to update schema descriptions"""
    name: Optional[str] = Field(None, description="Updated schema name", max_length=255)
    enriched_description: Optional[str] = Field(None, description="Updated schema description", max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "enriched_description": "Updated description for the schema"
            }
        }


class TableUpdateRequest(BaseModel):
    """Request to update table description"""
    table_id: UUID = Field(..., description="UUID of table to update")
    enriched_description: str = Field(..., description="Updated table description", max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "table_id": "123e4567-e89b-12d3-a456-426614174000",
                "enriched_description": "Updated description for the table"
            }
        }


class ColumnUpdateRequest(BaseModel):
    """Request to update column description"""
    column_id: UUID = Field(..., description="UUID of column to update")
    enriched_description: str = Field(..., description="Updated column description", max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "column_id": "123e4567-e89b-12d3-a456-426614174000",
                "enriched_description": "Updated description for the column"
            }
        }
