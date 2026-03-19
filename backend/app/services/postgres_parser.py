"""
PostgreSQL Schema Parser
Introspects PostgreSQL databases using information_schema
"""
from typing import List, Dict, Any, Optional
import asyncpg
import structlog

from app.services.schema_parser import (
    SchemaParser,
    TableInfo,
    ColumnInfo
)

logger = structlog.get_logger()


class PostgreSQLParser(SchemaParser):
    """
    PostgreSQL-specific schema parser

    Uses PostgreSQL's information_schema and system catalogs
    to extract complete database schema information
    """

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self) -> None:
        """Establish connection to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.connection_string)
            self.logger.info("Connected to PostgreSQL database")
        except Exception as e:
            self.logger.error("Failed to connect to PostgreSQL", error=str(e))
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self.conn:
            await self.conn.close()
            self.logger.info("Disconnected from PostgreSQL")

    async def get_tables(self) -> List[str]:
        """
        Get all table names from the public schema

        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """

        rows = await self.conn.fetch(query)
        return [row['table_name'] for row in rows]

    async def get_table_info(self, table_name: str) -> TableInfo:
        """
        Get detailed information about a PostgreSQL table

        Args:
            table_name: Name of the table

        Returns:
            TableInfo with columns and metadata
        """
        # Get column information
        columns = await self._get_columns(table_name)

        # Get primary keys
        primary_keys = await self._get_primary_keys(table_name)

        # Get foreign keys
        foreign_keys = await self._get_foreign_keys(table_name)

        # Get unique constraints
        unique_columns = await self._get_unique_columns(table_name)

        # Get row count
        row_count = await self._get_row_count(table_name)

        # Get table comment
        comment = await self._get_table_comment(table_name)

        # Enhance column info with constraints
        enhanced_columns = []
        for col in columns:
            col.is_primary_key = col.name in primary_keys
            col.is_unique = col.name in unique_columns

            # Check if foreign key
            if col.name in foreign_keys:
                col.is_foreign_key = True
                col.foreign_key_table = foreign_keys[col.name]['table']
                col.foreign_key_column = foreign_keys[col.name]['column']

            enhanced_columns.append(col)

        return TableInfo(
            name=table_name,
            columns=enhanced_columns,
            row_count=row_count,
            comment=comment
        )

    async def _get_columns(self, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table"""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = $1
            ORDER BY ordinal_position;
        """

        rows = await self.conn.fetch(query, table_name)

        columns = []
        for row in rows:
            # Normalize data type
            data_type = row['udt_name'] or row['data_type']
            normalized_type = self.normalize_type(data_type)

            # Check if auto-increment (serial)
            is_auto_increment = False
            if row['column_default']:
                default = row['column_default'].lower()
                is_auto_increment = 'nextval' in default

            column = ColumnInfo(
                name=row['column_name'],
                data_type=normalized_type,
                is_nullable=row['is_nullable'] == 'YES',
                is_primary_key=False,  # Will be set later
                is_foreign_key=False,  # Will be set later
                default_value=row['column_default'],
                max_length=row['character_maximum_length'],
                numeric_precision=row['numeric_precision'],
                numeric_scale=row['numeric_scale'],
                is_auto_increment=is_auto_increment
            )
            columns.append(column)

        return columns

    async def _get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key column names"""
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass
              AND i.indisprimary;
        """

        rows = await self.conn.fetch(query, f'public.{table_name}')
        return [row['attname'] for row in rows]

    async def _get_foreign_keys(
        self,
        table_name: str
    ) -> Dict[str, Dict[str, str]]:
        """
        Get foreign key information

        Returns:
            Dict mapping column name to {table, column}
        """
        query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = $1;
        """

        rows = await self.conn.fetch(query, table_name)

        foreign_keys = {}
        for row in rows:
            foreign_keys[row['column_name']] = {
                'table': row['foreign_table_name'],
                'column': row['foreign_column_name']
            }

        return foreign_keys

    async def _get_unique_columns(self, table_name: str) -> List[str]:
        """Get columns with unique constraints"""
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass
              AND i.indisunique
              AND NOT i.indisprimary;
        """

        rows = await self.conn.fetch(query, f'public.{table_name}')
        return [row['attname'] for row in rows]

    async def _get_row_count(self, table_name: str) -> Optional[int]:
        """Get approximate row count for a table"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table_name};"
            row = await self.conn.fetchrow(query)
            return row['count']
        except Exception as e:
            self.logger.warning(
                "Failed to get row count",
                table=table_name,
                error=str(e)
            )
            return None

    async def _get_table_comment(self, table_name: str) -> Optional[str]:
        """Get table comment/description"""
        query = """
            SELECT obj_description($1::regclass, 'pg_class') as comment;
        """

        row = await self.conn.fetchrow(query, f'public.{table_name}')
        return row['comment'] if row else None

    async def get_sample_data(
        self,
        table_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get sample rows from a table

        Args:
            table_name: Name of the table
            limit: Number of sample rows

        Returns:
            List of row dictionaries
        """
        try:
            query = f"SELECT * FROM {table_name} LIMIT $1;"
            rows = await self.conn.fetch(query, limit)

            # Convert to list of dicts
            sample_data = []
            for row in rows:
                row_dict = dict(row)
                # Convert non-serializable types to strings
                for key, value in row_dict.items():
                    if value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
                        row_dict[key] = str(value)
                sample_data.append(row_dict)

            return sample_data

        except Exception as e:
            self.logger.warning(
                "Failed to get sample data",
                table=table_name,
                error=str(e)
            )
            return []

    async def _get_db_version(self) -> Optional[str]:
        """Get PostgreSQL version"""
        try:
            row = await self.conn.fetchrow("SELECT version();")
            return row['version'] if row else None
        except Exception:
            return None

    def _get_db_type(self) -> str:
        """Get database type"""
        return "postgresql"
