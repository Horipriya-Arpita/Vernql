"""
Base module for importing all models
This is used by Alembic for migrations
"""
from app.db.database import Base

# Import all models here so Alembic can detect them
from app.models.company import Company
from app.models.api_key import APIKey
from app.models.schema import Schema, SchemaTable, SchemaColumn
from app.models.query import Query

# Export all models
__all__ = [
    "Base",
    "Company",
    "APIKey",
    "Schema",
    "SchemaTable",
    "SchemaColumn",
    "Query",
]
