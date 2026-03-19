"""
Quick test of schema parser
"""
import asyncio
from app.services.postgres_parser import PostgreSQLParser

async def test_parse():
    # Connection to our own database
    connection_string = "postgresql://textsql:textsql@127.0.0.1:5432/textsql"

    parser = PostgreSQLParser(connection_string)

    try:
        schema_info = await parser.parse_schema(
            include_sample_data=True,
            sample_limit=3
        )

        print(f"\n{'='*60}")
        print(f"Database: {schema_info.database_name}")
        print(f"Type: {schema_info.database_type}")
        print(f"Version: {schema_info.version}")
        print(f"Tables: {len(schema_info.tables)}")
        print(f"{'='*60}\n")

        for table in schema_info.tables[:5]:  # Show first 5 tables
            print(f"\n📋 Table: {table.name}")
            print(f"   Rows: {table.row_count}")
            print(f"   Columns: {len(table.columns)}")

            for col in table.columns[:10]:  # Show first 10 columns
                pk = " [PK]" if col.is_primary_key else ""
                fk = f" [FK->{col.foreign_key_table}]" if col.is_foreign_key else ""
                print(f"      • {col.name}: {col.data_type}{pk}{fk}")

            if table.sample_data:
                print(f"   Sample data: {len(table.sample_data)} rows")

        print(f"\n✅ Schema parsing successful!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parse())
