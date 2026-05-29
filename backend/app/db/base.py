"""
Base module for importing all models
This is used by Alembic for migrations — every model must be imported here
so that Alembic's autogenerate can detect it.
"""
from app.db.database import Base

# Core models
from app.models.company import Company
from app.models.api_key import APIKey
from app.models.user import User
from app.models.schema import Schema, SchemaTable, SchemaColumn
from app.models.query import Query
from app.models.query_result import QueryResult
from app.models.session import Session
from app.models.query_example import QueryExample

# Q2 new models
from app.models.audit_log import AuditLog
from app.models.webhook import Webhook

__all__ = [
    "Base",
    "Company",
    "APIKey",
    "User",
    "Schema",
    "SchemaTable",
    "SchemaColumn",
    "Query",
    "QueryResult",
    "Session",
    "QueryExample",
    "AuditLog",
    "Webhook",
]
