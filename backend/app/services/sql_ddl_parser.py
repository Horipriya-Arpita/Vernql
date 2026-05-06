"""
SQL DDL Parser
Parses SQL DDL statements to extract database schema information
This parser works with SQL text, NOT live database connections (privacy-first)
"""
import re
from typing import List, Dict, Optional, Tuple
import structlog

from app.services.schema_parser import SchemaInfo, TableInfo, ColumnInfo

logger = structlog.get_logger()


class SQLDDLParser:
    """
    Parse SQL DDL statements to extract schema structure

    Supports:
    - PostgreSQL DDL syntax
    - MySQL DDL syntax

    Does NOT require database credentials or access
    """

    def __init__(self, sql_ddl: str, db_type: str):
        """
        Initialize parser with SQL DDL text

        Args:
            sql_ddl: SQL DDL statements (CREATE TABLE, etc.)
            db_type: Database type ('postgresql' or 'mysql')
        """
        self.sql_ddl = sql_ddl
        self.db_type = db_type.lower()
        self.logger = logger.bind(parser="SQLDDLParser", db_type=db_type)

    def parse(self) -> SchemaInfo:
        """
        Parse SQL DDL and extract schema information

        Returns:
            SchemaInfo object with tables and columns
        """
        self.logger.info("Parsing SQL DDL", ddl_length=len(self.sql_ddl))

        # Extract all CREATE TABLE statements
        tables = self._extract_tables()

        self.logger.info("Parsed SQL DDL", table_count=len(tables))

        return SchemaInfo(
            database_name="uploaded_schema",
            database_type=self.db_type,
            tables=tables,
            version=None
        )

    def _extract_tables(self) -> List[TableInfo]:
        """Extract all tables from SQL DDL"""
        tables = []

        # Find all CREATE TABLE statements
        # Match: CREATE TABLE table_name (...); or CREATE TABLE IF NOT EXISTS table_name (...);
        pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`)?([a-zA-Z0-9_]+)(?:`)?\s*\((.*?)\);'

        matches = re.finditer(pattern, self.sql_ddl, re.IGNORECASE | re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            table_definition = match.group(2)

            self.logger.debug("Found table", table_name=table_name)

            # Parse columns from table definition
            columns = self._parse_columns(table_name, table_definition)

            # Parse foreign keys
            foreign_keys = self._parse_foreign_keys(table_definition)
            self._apply_foreign_keys(columns, foreign_keys)

            tables.append(TableInfo(
                name=table_name,
                columns=columns,
                row_count=None,
                comment=None,
                sample_data=None
            ))

        return tables

    def _parse_columns(self, table_name: str, table_def: str) -> List[ColumnInfo]:
        """Parse column definitions from CREATE TABLE statement"""
        columns = []

        # Split by commas, but be careful with commas inside constraints
        lines = self._split_table_definition(table_def)

        primary_keys = self._extract_primary_keys(table_def)

        for line in lines:
            line = line.strip()

            # Skip constraint definitions (PRIMARY KEY, FOREIGN KEY, INDEX, etc.)
            if any(keyword in line.upper() for keyword in [
                'PRIMARY KEY', 'FOREIGN KEY', 'CONSTRAINT',
                'INDEX', 'KEY ', 'UNIQUE KEY', 'FULLTEXT'
            ]) and not line.upper().startswith(('ALTER', 'ADD')):
                # Check if it's an inline column definition with these keywords
                if not re.match(r'^`?[a-zA-Z0-9_]+`?\s+', line):
                    continue

            # Parse column definition
            column = self._parse_column_line(line, primary_keys)
            if column:
                columns.append(column)

        return columns

    def _split_table_definition(self, table_def: str) -> List[str]:
        """Split table definition by commas, respecting parentheses"""
        lines = []
        current = ""
        paren_depth = 0

        for char in table_def:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                lines.append(current.strip())
                current = ""
                continue

            current += char

        if current.strip():
            lines.append(current.strip())

        return lines

    def _extract_primary_keys(self, table_def: str) -> List[str]:
        """Extract primary key column names"""
        primary_keys = []

        # Pattern 1: PRIMARY KEY (col1, col2)
        pattern = r'PRIMARY\s+KEY\s*\(([^)]+)\)'
        matches = re.finditer(pattern, table_def, re.IGNORECASE)

        for match in matches:
            keys_str = match.group(1)
            # Remove backticks and split by comma
            keys = [k.strip().strip('`').strip('"') for k in keys_str.split(',')]
            primary_keys.extend(keys)

        return primary_keys

    def _parse_column_line(self, line: str, primary_keys: List[str]) -> Optional[ColumnInfo]:
        """Parse a single column definition line"""
        # Match: column_name DATA_TYPE [constraints]
        # Examples:
        # id INT PRIMARY KEY
        # email VARCHAR(255) NOT NULL
        # `user_id` INTEGER REFERENCES users(id)

        # Extract column name (with optional backticks/quotes)
        match = re.match(r'^(?:`|")?([a-zA-Z0-9_]+)(?:`|")?\s+(.+)$', line, re.IGNORECASE)

        if not match:
            return None

        column_name = match.group(1)
        rest = match.group(2).strip()

        # Extract data type (first word or first word with parentheses)
        data_type_match = re.match(r'^([A-Z0-9_]+(?:\([^)]*\))?)', rest, re.IGNORECASE)
        if not data_type_match:
            return None

        data_type = data_type_match.group(1)
        constraints = rest[len(data_type):].strip().upper()

        # Determine column properties
        is_nullable = 'NOT NULL' not in constraints
        is_primary_key = 'PRIMARY KEY' in constraints or column_name in primary_keys
        is_foreign_key = 'REFERENCES' in constraints
        is_auto_increment = any(kw in constraints for kw in ['AUTO_INCREMENT', 'SERIAL', 'AUTOINCREMENT'])
        is_unique = 'UNIQUE' in constraints

        # Extract default value
        default_value = None
        default_match = re.search(r'DEFAULT\s+([^\s,]+)', constraints)
        if default_match:
            default_value = default_match.group(1)

        # Extract foreign key reference
        foreign_key_table = None
        foreign_key_column = None
        if is_foreign_key:
            fk_match = re.search(r'REFERENCES\s+(?:`)?([a-zA-Z0-9_]+)(?:`)?\s*\((?:`)?([a-zA-Z0-9_]+)(?:`)?\)', rest, re.IGNORECASE)
            if fk_match:
                foreign_key_table = fk_match.group(1)
                foreign_key_column = fk_match.group(2)

        return ColumnInfo(
            name=column_name,
            data_type=data_type,
            is_nullable=is_nullable,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            foreign_key_table=foreign_key_table,
            foreign_key_column=foreign_key_column,
            default_value=default_value,
            is_unique=is_unique,
            is_auto_increment=is_auto_increment,
            comment=None
        )

    def _parse_foreign_keys(self, table_def: str) -> List[Tuple[str, str, str]]:
        """
        Parse FOREIGN KEY constraints

        Returns:
            List of (column_name, referenced_table, referenced_column)
        """
        foreign_keys = []

        # Pattern: FOREIGN KEY (column) REFERENCES table(column)
        pattern = r'FOREIGN\s+KEY\s*\((?:`)?([a-zA-Z0-9_]+)(?:`)?\)\s*REFERENCES\s+(?:`)?([a-zA-Z0-9_]+)(?:`)?\s*\((?:`)?([a-zA-Z0-9_]+)(?:`)?\)'

        matches = re.finditer(pattern, table_def, re.IGNORECASE)

        for match in matches:
            column_name = match.group(1)
            ref_table = match.group(2)
            ref_column = match.group(3)
            foreign_keys.append((column_name, ref_table, ref_column))

        return foreign_keys

    def _apply_foreign_keys(self, columns: List[ColumnInfo], foreign_keys: List[Tuple[str, str, str]]):
        """Apply foreign key constraints to columns"""
        for col_name, ref_table, ref_column in foreign_keys:
            for column in columns:
                if column.name == col_name:
                    column.is_foreign_key = True
                    column.foreign_key_table = ref_table
                    column.foreign_key_column = ref_column
                    break


def parse_sql_ddl(sql_ddl: str, db_type: str) -> SchemaInfo:
    """
    Convenience function to parse SQL DDL

    Args:
        sql_ddl: SQL DDL statements
        db_type: Database type ('postgresql' or 'mysql')

    Returns:
        SchemaInfo object
    """
    parser = SQLDDLParser(sql_ddl, db_type)
    return parser.parse()