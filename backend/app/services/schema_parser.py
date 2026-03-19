"""
Schema Parser Base Classes and Types
Provides abstract interface for database schema introspection
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class ColumnType(str, Enum):
    """Common column types across databases"""
    INTEGER = "integer"
    BIGINT = "bigint"
    SMALLINT = "smallint"
    DECIMAL = "decimal"
    NUMERIC = "numeric"
    REAL = "real"
    DOUBLE = "double"
    VARCHAR = "varchar"
    CHAR = "char"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    DATETIME = "datetime"
    JSON = "json"
    JSONB = "jsonb"
    UUID = "uuid"
    BINARY = "binary"
    ARRAY = "array"
    ENUM = "enum"
    OTHER = "other"


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: Optional[str] = None
    foreign_key_column: Optional[str] = None
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    is_unique: bool = False
    is_auto_increment: bool = False
    comment: Optional[str] = None


@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    columns: List[ColumnInfo]
    row_count: Optional[int] = None
    comment: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None


@dataclass
class SchemaInfo:
    """Complete database schema information"""
    database_name: str
    database_type: str  # postgresql, mysql
    tables: List[TableInfo]
    version: Optional[str] = None


class SchemaParser(ABC):
    """
    Abstract base class for database schema parsers

    Implementations should provide database-specific introspection logic
    """

    def __init__(self, connection_string: str):
        """
        Initialize parser with database connection string

        Args:
            connection_string: Database connection URL
                PostgreSQL: postgresql://user:pass@host:port/dbname
                MySQL: mysql://user:pass@host:port/dbname
        """
        self.connection_string = connection_string
        self.logger = logger.bind(parser=self.__class__.__name__)

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the database

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def get_tables(self) -> List[str]:
        """
        Get list of all table names in the database

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    async def get_table_info(self, table_name: str) -> TableInfo:
        """
        Get detailed information about a specific table

        Args:
            table_name: Name of the table to introspect

        Returns:
            TableInfo object with complete table metadata
        """
        pass

    @abstractmethod
    async def get_sample_data(
        self,
        table_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get sample rows from a table

        Args:
            table_name: Name of the table
            limit: Number of sample rows to retrieve

        Returns:
            List of dictionaries representing sample rows
        """
        pass

    async def parse_schema(
        self,
        include_sample_data: bool = True,
        sample_limit: int = 5
    ) -> SchemaInfo:
        """
        Parse complete database schema

        Args:
            include_sample_data: Whether to include sample data for tables
            sample_limit: Number of sample rows per table

        Returns:
            SchemaInfo object with complete schema information
        """
        try:
            await self.connect()

            # Get all tables
            table_names = await self.get_tables()
            self.logger.info(
                "Found tables",
                count=len(table_names),
                tables=table_names
            )

            # Get detailed info for each table
            tables = []
            for table_name in table_names:
                try:
                    table_info = await self.get_table_info(table_name)

                    # Optionally add sample data
                    if include_sample_data:
                        sample_data = await self.get_sample_data(
                            table_name,
                            limit=sample_limit
                        )
                        table_info.sample_data = sample_data

                    tables.append(table_info)

                    self.logger.info(
                        "Parsed table",
                        table=table_name,
                        columns=len(table_info.columns)
                    )

                except Exception as e:
                    self.logger.error(
                        "Failed to parse table",
                        table=table_name,
                        error=str(e)
                    )
                    # Continue with other tables
                    continue

            # Create schema info
            schema_info = SchemaInfo(
                database_name=self._extract_db_name(),
                database_type=self._get_db_type(),
                tables=tables,
                version=await self._get_db_version()
            )

            self.logger.info(
                "Schema parsing complete",
                database=schema_info.database_name,
                tables=len(schema_info.tables)
            )

            return schema_info

        finally:
            await self.disconnect()

    @abstractmethod
    async def _get_db_version(self) -> Optional[str]:
        """Get database version string"""
        pass

    def _extract_db_name(self) -> str:
        """Extract database name from connection string"""
        # postgresql://user:pass@host:port/dbname
        # mysql://user:pass@host:port/dbname
        parts = self.connection_string.split('/')
        if len(parts) >= 4:
            # Remove query params if any
            db_name = parts[-1].split('?')[0]
            return db_name
        return "unknown"

    @abstractmethod
    def _get_db_type(self) -> str:
        """Get database type (postgresql, mysql)"""
        pass

    def normalize_type(self, db_type: str) -> str:
        """
        Normalize database-specific type to common type

        Args:
            db_type: Database-specific type name

        Returns:
            Normalized type name
        """
        db_type = db_type.lower()

        # Integer types
        if any(t in db_type for t in ['int', 'integer', 'serial']):
            if 'big' in db_type:
                return ColumnType.BIGINT.value
            elif 'small' in db_type:
                return ColumnType.SMALLINT.value
            return ColumnType.INTEGER.value

        # Decimal types
        if any(t in db_type for t in ['decimal', 'numeric', 'number']):
            return ColumnType.DECIMAL.value

        # Float types
        if any(t in db_type for t in ['real', 'float']):
            return ColumnType.REAL.value
        if any(t in db_type for t in ['double']):
            return ColumnType.DOUBLE.value

        # String types
        if any(t in db_type for t in ['varchar', 'character varying']):
            return ColumnType.VARCHAR.value
        if 'char' in db_type:
            return ColumnType.CHAR.value
        if 'text' in db_type:
            return ColumnType.TEXT.value

        # Boolean
        if any(t in db_type for t in ['bool', 'boolean']):
            return ColumnType.BOOLEAN.value

        # Date/Time types
        if db_type == 'date':
            return ColumnType.DATE.value
        if 'time' in db_type and 'stamp' in db_type:
            return ColumnType.TIMESTAMP.value
        if 'time' in db_type:
            return ColumnType.TIME.value
        if 'datetime' in db_type:
            return ColumnType.DATETIME.value

        # JSON
        if db_type == 'json':
            return ColumnType.JSON.value
        if db_type == 'jsonb':
            return ColumnType.JSONB.value

        # UUID
        if db_type == 'uuid':
            return ColumnType.UUID.value

        # Binary
        if any(t in db_type for t in ['binary', 'blob', 'bytea']):
            return ColumnType.BINARY.value

        # Array
        if 'array' in db_type or db_type.endswith('[]'):
            return ColumnType.ARRAY.value

        # Enum
        if 'enum' in db_type:
            return ColumnType.ENUM.value

        return ColumnType.OTHER.value
