"""
Quick Database Explorer
Run this script to view your database contents
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.models import Company, APIKey, Schema, SchemaTable, SchemaColumn, Query

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def explore_database():
    db = SessionLocal()
    try:
        # Companies
        print_section("COMPANIES")
        companies = db.query(Company).all()
        for company in companies:
            print(f"📊 {company.name}")
            print(f"   ID: {company.id}")
            print(f"   Active: {company.is_active}")
            print(f"   Created: {company.created_at}")

        # API Keys
        print_section("API KEYS")
        api_keys = db.query(APIKey).all()
        for key in api_keys:
            print(f"🔑 {key.name or 'Unnamed'}")
            print(f"   ID: {key.id}")
            print(f"   Active: {key.is_active}")
            print(f"   Rate Limits: {key.rate_limit_per_minute}/min, {key.rate_limit_per_hour}/hour")
            print(f"   Hash: {key.key_hash[:20]}...")

        # Schemas
        print_section("DATABASE SCHEMAS")
        schemas = db.query(Schema).all()
        for schema in schemas:
            print(f"🗄️  {schema.name} ({schema.db_type.value})")
            print(f"   ID: {schema.id}")
            print(f"   Description: {schema.enriched_description}")
            print(f"   Tables: {len(schema.tables)}")

            # Tables
            for table in schema.tables:
                print(f"\n   📋 Table: {table.name}")
                print(f"      {table.enriched_description}")
                print(f"      Columns ({len(table.columns)}):")

                # Columns
                for col in table.columns:
                    pk_marker = " [PK]" if col.is_primary_key else ""
                    fk_marker = f" [FK -> {col.foreign_key_table}.{col.foreign_key_column}]" if col.is_foreign_key else ""
                    null_marker = " NULL" if col.is_nullable else " NOT NULL"
                    print(f"         • {col.name}: {col.data_type}{pk_marker}{fk_marker}{null_marker}")
                    if col.enriched_description:
                        print(f"           └─ {col.enriched_description}")

        # Queries
        print_section("QUERY HISTORY")
        queries = db.query(Query).order_by(Query.created_at.desc()).limit(5).all()
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. 💬 {query.natural_language_query}")
            print(f"   Status: {query.status.value} | Confidence: {query.confidence_score:.2%}")
            print(f"   Time: {query.execution_time_ms}ms | Results: {query.result_count} rows")
            print(f"   SQL Preview: {query.generated_sql[:100]}...")

        print_section("SUMMARY")
        print(f"✅ Companies: {db.query(Company).count()}")
        print(f"✅ API Keys: {db.query(APIKey).count()}")
        print(f"✅ Schemas: {db.query(Schema).count()}")
        print(f"✅ Tables: {db.query(SchemaTable).count()}")
        print(f"✅ Columns: {db.query(SchemaColumn).count()}")
        print(f"✅ Queries: {db.query(Query).count()}")

        print("\n" + "=" * 60)
        print("🎉 Database is ready!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error exploring database: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔍 Exploring TextSQL Database...\n")
    explore_database()
