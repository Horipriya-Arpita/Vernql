#!/usr/bin/env python
"""
SQL Query Testing Script
Test if your SQL queries work against your database
"""
import sys
import os
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_sql_query(connection_string: str, sql: str) -> Dict[str, Any]:
    """
    Test a SQL query against a database

    Args:
        connection_string: Database connection string (postgresql:// or mysql://)
        sql: SQL query to execute

    Returns:
        Dictionary with success status, results, and error info
    """
    result = {
        "success": False,
        "rows": [],
        "row_count": 0,
        "columns": [],
        "error": None
    }

    engine = None
    connection = None

    try:
        # Create engine
        engine = create_engine(connection_string)
        connection = engine.connect()

        # Execute query
        db_result = connection.execute(text(sql))

        # Get column names
        if db_result.returns_rows:
            result["columns"] = list(db_result.keys())

            # Fetch results
            rows = db_result.fetchall()
            result["row_count"] = len(rows)

            # Convert rows to list of dicts
            result["rows"] = [
                {col: val for col, val in zip(result["columns"], row)}
                for row in rows
            ]
        else:
            result["row_count"] = db_result.rowcount

        result["success"] = True

    except SQLAlchemyError as e:
        result["error"] = str(e)
        result["success"] = False

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        result["success"] = False

    finally:
        if connection:
            connection.close()
        if engine:
            engine.dispose()

    return result


def format_result(result: Dict[str, Any], verbose: bool = False) -> str:
    """Format the query result for display"""
    output = []

    if result["success"]:
        output.append("✅ Query executed successfully!")
        output.append(f"\n📊 Results: {result['row_count']} rows")

        if result["columns"]:
            output.append(f"\n📋 Columns: {', '.join(result['columns'])}")

            if verbose and result["rows"]:
                output.append("\n📄 Sample Data (first 5 rows):")
                for i, row in enumerate(result["rows"][:5], 1):
                    output.append(f"\n  Row {i}:")
                    for col, val in row.items():
                        output.append(f"    {col}: {val}")
    else:
        output.append("❌ Query failed!")
        output.append(f"\n🚫 Error: {result['error']}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Test SQL queries against a database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a simple query
  python test_sql_queries.py -c "postgresql://user:pass@localhost:5432/mydb" -q "SELECT * FROM users LIMIT 5"

  # Test with verbose output
  python test_sql_queries.py -c "postgresql://user:pass@localhost:5432/mydb" -q "SELECT * FROM orders" -v

  # Test MySQL
  python test_sql_queries.py -c "mysql://user:pass@localhost:3306/mydb" -q "SELECT COUNT(*) FROM products"

  # Read query from file
  python test_sql_queries.py -c "postgresql://user:pass@localhost:5432/mydb" -f query.sql
        """
    )

    parser.add_argument(
        "-c", "--connection",
        required=True,
        help="Database connection string (postgresql:// or mysql://)"
    )

    parser.add_argument(
        "-q", "--query",
        help="SQL query to execute"
    )

    parser.add_argument(
        "-f", "--file",
        help="Read SQL query from file"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed results including sample data"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Get SQL query
    if args.query:
        sql = args.query
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                sql = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            sys.exit(1)
    else:
        print("❌ Error: Either --query or --file must be provided")
        parser.print_help()
        sys.exit(1)

    # Print header
    if not args.json:
        print("=" * 70)
        print("SQL QUERY TESTER")
        print("=" * 70)
        print(f"\n🔗 Connection: {args.connection[:50]}...")
        print(f"\n📝 Query:\n{sql}\n")
        print("=" * 70)

    # Execute query
    result = test_sql_query(args.connection, sql)

    # Output results
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(format_result(result, args.verbose))
        print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
