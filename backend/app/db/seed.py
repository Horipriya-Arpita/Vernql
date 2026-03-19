"""
Database Seed Data
Populates the database with sample data for testing and development
"""
import asyncio
from sqlalchemy.orm import Session
import hashlib
import secrets
from datetime import datetime, timezone

from app.db.database import SessionLocal
from app.models import (
    Company,
    APIKey,
    Schema,
    SchemaTable,
    SchemaColumn,
    Query,
    DatabaseType,
    QueryStatus,
)
import structlog

logger = structlog.get_logger()


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()


def create_sample_company(db: Session) -> Company:
    """Create a sample company"""
    company = Company(
        name="Acme Corporation",
        is_active=True,
    )
    db.add(company)
    db.flush()
    logger.info("Created sample company", company_id=str(company.id))
    return company


def create_sample_api_key(db: Session, company: Company) -> str:
    """Create a sample API key and return the unhashed key"""
    # Generate a sample API key
    raw_key = f"textsql_test_{secrets.token_urlsafe(32)}"

    api_key = APIKey(
        company_id=company.id,
        key_hash=hash_api_key(raw_key),
        name="Development Key",
        is_active=True,
        rate_limit_per_minute=100,
        rate_limit_per_hour=5000,
    )
    db.add(api_key)
    db.flush()
    logger.info("Created sample API key", api_key_id=str(api_key.id))
    return raw_key


def create_sample_schema(db: Session, company: Company) -> Schema:
    """Create a sample database schema"""
    schema = Schema(
        company_id=company.id,
        name="ecommerce_db",
        db_type=DatabaseType.POSTGRESQL,
        enriched_description="E-commerce database containing users, products, orders, and related entities",
        is_active=True,
        enriched_at=datetime.now(timezone.utc),
    )
    db.add(schema)
    db.flush()
    logger.info("Created sample schema", schema_id=str(schema.id))
    return schema


def create_sample_tables(db: Session, schema: Schema):
    """Create sample tables with columns"""

    # Users table
    users_table = SchemaTable(
        schema_id=schema.id,
        name="users",
        enriched_description="Customer accounts and authentication information",
        sample_values={
            "sample_rows": [
                {"id": 1, "email": "john@example.com", "name": "John Doe"},
                {"id": 2, "email": "jane@example.com", "name": "Jane Smith"},
            ]
        },
    )
    db.add(users_table)
    db.flush()

    # Users columns
    users_columns = [
        SchemaColumn(
            table_id=users_table.id,
            name="id",
            data_type="integer",
            is_primary_key=True,
            is_nullable=False,
            enriched_description="Unique user identifier",
        ),
        SchemaColumn(
            table_id=users_table.id,
            name="email",
            data_type="varchar(255)",
            is_nullable=False,
            enriched_description="User's email address for login",
        ),
        SchemaColumn(
            table_id=users_table.id,
            name="name",
            data_type="varchar(255)",
            is_nullable=False,
            enriched_description="User's full name",
        ),
        SchemaColumn(
            table_id=users_table.id,
            name="created_at",
            data_type="timestamp",
            is_nullable=False,
            enriched_description="Account creation timestamp",
        ),
    ]
    db.add_all(users_columns)

    # Products table
    products_table = SchemaTable(
        schema_id=schema.id,
        name="products",
        enriched_description="Product catalog with pricing and inventory",
        sample_values={
            "sample_rows": [
                {"id": 1, "name": "Widget", "price": 29.99, "stock": 100},
                {"id": 2, "name": "Gadget", "price": 49.99, "stock": 50},
            ]
        },
    )
    db.add(products_table)
    db.flush()

    # Products columns
    products_columns = [
        SchemaColumn(
            table_id=products_table.id,
            name="id",
            data_type="integer",
            is_primary_key=True,
            is_nullable=False,
            enriched_description="Unique product identifier",
        ),
        SchemaColumn(
            table_id=products_table.id,
            name="name",
            data_type="varchar(255)",
            is_nullable=False,
            enriched_description="Product name",
        ),
        SchemaColumn(
            table_id=products_table.id,
            name="price",
            data_type="decimal(10,2)",
            is_nullable=False,
            enriched_description="Product price in USD",
        ),
        SchemaColumn(
            table_id=products_table.id,
            name="stock",
            data_type="integer",
            is_nullable=False,
            enriched_description="Available inventory quantity",
        ),
    ]
    db.add_all(products_columns)

    # Orders table
    orders_table = SchemaTable(
        schema_id=schema.id,
        name="orders",
        enriched_description="Customer orders and purchase history",
        sample_values={
            "sample_rows": [
                {"id": 1, "user_id": 1, "total": 79.98, "status": "completed"},
                {"id": 2, "user_id": 2, "total": 49.99, "status": "pending"},
            ]
        },
    )
    db.add(orders_table)
    db.flush()

    # Orders columns
    orders_columns = [
        SchemaColumn(
            table_id=orders_table.id,
            name="id",
            data_type="integer",
            is_primary_key=True,
            is_nullable=False,
            enriched_description="Unique order identifier",
        ),
        SchemaColumn(
            table_id=orders_table.id,
            name="user_id",
            data_type="integer",
            is_foreign_key=True,
            foreign_key_table="users",
            foreign_key_column="id",
            is_nullable=False,
            enriched_description="Customer who placed the order",
        ),
        SchemaColumn(
            table_id=orders_table.id,
            name="total",
            data_type="decimal(10,2)",
            is_nullable=False,
            enriched_description="Order total amount",
        ),
        SchemaColumn(
            table_id=orders_table.id,
            name="status",
            data_type="varchar(50)",
            is_nullable=False,
            enriched_description="Order status (pending, completed, cancelled)",
        ),
        SchemaColumn(
            table_id=orders_table.id,
            name="created_at",
            data_type="timestamp",
            is_nullable=False,
            enriched_description="Order creation timestamp",
        ),
    ]
    db.add_all(orders_columns)

    db.flush()
    logger.info("Created sample tables and columns")


def create_sample_queries(db: Session, company: Company, schema: Schema):
    """Create sample query history"""

    queries = [
        Query(
            company_id=company.id,
            schema_id=schema.id,
            natural_language_query="Show me all users who signed up in the last 30 days",
            generated_sql="SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '30 days'",
            ai_provider="openai",
            ai_model="gpt-4o",
            confidence_score=0.95,
            status=QueryStatus.SUCCESS,
            execution_time_ms=45,
            result_count=127,
        ),
        Query(
            company_id=company.id,
            schema_id=schema.id,
            natural_language_query="What are the top 5 best-selling products?",
            generated_sql="""
                SELECT p.id, p.name, COUNT(oi.id) as order_count
                FROM products p
                JOIN order_items oi ON p.id = oi.product_id
                GROUP BY p.id, p.name
                ORDER BY order_count DESC
                LIMIT 5
            """,
            ai_provider="openai",
            ai_model="gpt-4o",
            confidence_score=0.89,
            status=QueryStatus.SUCCESS,
            execution_time_ms=67,
            result_count=5,
        ),
        Query(
            company_id=company.id,
            schema_id=schema.id,
            natural_language_query="Calculate total revenue by month",
            generated_sql="""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    SUM(total) as revenue
                FROM orders
                WHERE status = 'completed'
                GROUP BY month
                ORDER BY month DESC
            """,
            ai_provider="openai",
            ai_model="gpt-4o",
            confidence_score=0.92,
            status=QueryStatus.SUCCESS,
            execution_time_ms=123,
            result_count=12,
        ),
    ]

    db.add_all(queries)
    db.flush()
    logger.info("Created sample queries", count=len(queries))


def seed_database():
    """Main seed function"""
    db = SessionLocal()
    try:
        logger.info("Starting database seeding...")

        # Create sample data
        company = create_sample_company(db)
        api_key = create_sample_api_key(db, company)
        schema = create_sample_schema(db, company)
        create_sample_tables(db, schema)
        create_sample_queries(db, company, schema)

        # Commit all changes
        db.commit()

        logger.info("Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("SAMPLE DATA CREATED:")
        logger.info(f"Company: {company.name} (ID: {company.id})")
        logger.info(f"API Key: {api_key}")
        logger.info(f"Schema: {schema.name} (ID: {schema.id})")
        logger.info("=" * 60)
        logger.info("Save the API key above - it won't be shown again!")

    except Exception as e:
        logger.error("Error seeding database", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
