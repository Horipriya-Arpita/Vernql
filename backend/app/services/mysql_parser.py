"""
MySQL Schema Parser
Introspects MySQL databases using information_schema
"""
from typing import List, Dict, Any, Optional
import aiomysql
from urllib.parse import urlparse
import structlog

from app.services.schema_parser import (
    SchemaParser,
    TableInfo,
    ColumnInfo
)

logger = structlog.get_logger()


class MySQLParser(SchemaParser):
    """
    MySQL-specific schema parser

    Uses MySQL's information_schema to extract complete database schema information
    """

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.conn: Optional[aiomysql.Connection] = None
        self.db_name: Optional[str] = None

    async def connect(self) -> None:
        """Establish connection to MySQL database"""
        try:
            # Parse connection string
            # mysql://user:pass@host:port/dbname
            parsed = urlparse(self.connection_string)
            self.db_name = parsed.path.lstrip('/')

            self.conn = await aiomysql.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                db=self.db_name,
                charset='utf8mb4'
            )
            self.logger.info("Connected to MySQL database", database=self.db_name)
        except Exception as e:
            self.logger.error("Failed to connect to MySQL", error=str(e))
            raise ConnectionError(f"Failed to connect to MySQL: {e}")

    async def disconnect(self) -> None:
        """Close MySQL connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Disconnected from MySQL")

    async def get_tables(self) -> List[str]:
        """
        Get all table names from the database

        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name,))
            rows = await cursor.fetchall()
            return [row['table_name'] for row in rows]

    async def get_table_info(self, table_name: str) -> TableInfo:
        """
        Get detailed information about a MySQL table

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
                extra,
                column_comment
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position;
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name, table_name))
            rows = await cursor.fetchall()

            columns = []
            for row in rows:
                # Normalize data type
                data_type = row['data_type']
                normalized_type = self.normalize_type(data_type)

                # Check if auto-increment
                is_auto_increment = 'auto_increment' in row['extra'].lower()

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
                    is_auto_increment=is_auto_increment,
                    comment=row['column_comment'] if row['column_comment'] else None
                )
                columns.append(column)

            return columns

    async def _get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key column names"""
        query = """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s
              AND table_name = %s
              AND constraint_name = 'PRIMARY'
            ORDER BY ordinal_position;
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name, table_name))
            rows = await cursor.fetchall()
            return [row['column_name'] for row in rows]

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
                column_name,
                referenced_table_name,
                referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_schema = %s
              AND table_name = %s
              AND referenced_table_name IS NOT NULL;
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name, table_name))
            rows = await cursor.fetchall()

            foreign_keys = {}
            for row in rows:
                foreign_keys[row['column_name']] = {
                    'table': row['referenced_table_name'],
                    'column': row['referenced_column_name']
                }

            return foreign_keys

    async def _get_unique_columns(self, table_name: str) -> List[str]:
        """Get columns with unique constraints"""
        query = """
            SELECT column_name
            FROM information_schema.statistics
            WHERE table_schema = %s
              AND table_name = %s
              AND non_unique = 0
              AND index_name != 'PRIMARY';
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name, table_name))
            rows = await cursor.fetchall()
            return [row['column_name'] for row in rows]

    async def _get_row_count(self, table_name: str) -> Optional[int]:
        """Get approximate row count for a table"""
        try:
            query = f"SELECT COUNT(*) as count FROM `{table_name}`;"
            async with self.conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                row = await cursor.fetchone()
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
            SELECT table_comment
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_name = %s;
        """

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (self.db_name, table_name))
            row = await cursor.fetchone()
            if row and row['table_comment']:
                return row['table_comment']
            return None

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
            query = f"SELECT * FROM `{table_name}` LIMIT %s;"
            async with self.conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (limit,))
                rows = await cursor.fetchall()

                # Convert to list of dicts with serializable types
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
        """Get MySQL version"""
        try:
            query = "SELECT VERSION() as version;"
            async with self.conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                row = await cursor.fetchone()
                return row['version'] if row else None
        except Exception:
            return None

    def _get_db_type(self) -> str:
        """Get database type"""
        return "mysql"
