"""
SQL Validator Service
Validates generated SQL for security, correctness, and best practices
"""
from typing import List, Dict, Optional, Set
import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML
import structlog

from app.models import Schema, SchemaTable

logger = structlog.get_logger()


class ValidationWarning:
    """Represents a validation warning"""

    def __init__(
        self,
        severity: str,  # "error", "warning", "info"
        message: str,
        code: str,
        suggestion: Optional[str] = None
    ):
        self.severity = severity
        self.message = message
        self.code = code
        self.suggestion = suggestion

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "severity": self.severity,
            "message": self.message,
            "code": self.code,
            "suggestion": self.suggestion
        }


class SQLValidator:
    """
    Comprehensive SQL validator for security and best practices

    Features:
    - Forbidden keyword detection (DML operations)
    - SQL injection pattern detection
    - Table/column existence validation
    - LIMIT clause enforcement
    - JOIN syntax validation
    - Best practice checks
    """

    # Dangerous keywords that should never appear in read-only queries
    FORBIDDEN_KEYWORDS = {
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
        'INSERT', 'UPDATE', 'EXEC', 'EXECUTE', 'GRANT',
        'REVOKE', 'RENAME', 'REPLACE'
    }

    # Suspicious patterns that might indicate SQL injection
    INJECTION_PATTERNS = [
        r';\s*DROP',  # Statement chaining
        r'--',  # SQL comments
        r'/\*.*\*/',  # Block comments
        r'UNION\s+SELECT',  # Union-based injection
        r'OR\s+1\s*=\s*1',  # Always-true conditions
        r'OR\s+\'1\'\s*=\s*\'1\'',
        r'SLEEP\s*\(',  # Time-based injection
        r'BENCHMARK\s*\(',
        r'WAITFOR\s+DELAY',
    ]

    def __init__(self):
        self.logger = logger.bind(service="sql_validator")

    def validate(
        self,
        sql: str,
        schema: Optional[Schema] = None,
        db_type: str = "postgresql"
    ) -> List[ValidationWarning]:
        """
        Comprehensive SQL validation

        Args:
            sql: SQL query to validate
            schema: Schema object for table/column validation
            db_type: Database type (postgresql, mysql)

        Returns:
            List of validation warnings (empty if all checks pass)
        """
        warnings = []

        # Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                warnings.append(ValidationWarning(
                    severity="error",
                    message="Invalid SQL: Unable to parse query",
                    code="INVALID_SQL"
                ))
                return warnings
        except Exception as e:
            warnings.append(ValidationWarning(
                severity="error",
                message=f"SQL parsing failed: {str(e)}",
                code="PARSE_ERROR"
            ))
            return warnings

        # Run all validation checks
        warnings.extend(self._check_forbidden_keywords(sql))
        warnings.extend(self._check_injection_patterns(sql))
        warnings.extend(self._check_limit_clause(sql, db_type))

        if schema:
            warnings.extend(self._check_table_references(sql, schema))
            warnings.extend(self._check_column_references(sql, schema))

        warnings.extend(self._check_best_practices(sql, parsed[0] if parsed else None))

        # Log validation results
        if warnings:
            error_count = sum(1 for w in warnings if w.severity == "error")
            warning_count = sum(1 for w in warnings if w.severity == "warning")
            self.logger.warning(
                "SQL validation issues found",
                errors=error_count,
                warnings=warning_count,
                sql_preview=sql[:100]
            )

        return warnings

    def _check_forbidden_keywords(self, sql: str) -> List[ValidationWarning]:
        """Check for forbidden/dangerous keywords"""
        warnings = []
        sql_upper = sql.upper()

        for keyword in self.FORBIDDEN_KEYWORDS:
            # Match keyword as whole word only (not within identifiers)
            pattern = r'\b' + keyword + r'\b'
            match = re.search(pattern, sql_upper)

            if match:
                # Get context around the match
                start = max(0, match.start() - 20)
                end = min(len(sql_upper), match.end() + 20)
                context = sql_upper[start:end]

                self.logger.error(
                    "Forbidden keyword detected",
                    keyword=keyword,
                    position=match.span(),
                    context=context
                )

                warnings.append(ValidationWarning(
                    severity="error",
                    message=f"Forbidden keyword detected: {keyword}",
                    code="FORBIDDEN_KEYWORD",
                    suggestion="This operation is not allowed. Only SELECT queries are permitted."
                ))

        return warnings

    def _check_injection_patterns(self, sql: str) -> List[ValidationWarning]:
        """Check for SQL injection patterns"""
        warnings = []

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(ValidationWarning(
                    severity="error",
                    message=f"Suspicious SQL pattern detected: {pattern}",
                    code="INJECTION_PATTERN",
                    suggestion="Query contains patterns commonly used in SQL injection attacks"
                ))

        return warnings

    def _check_limit_clause(self, sql: str, db_type: str) -> List[ValidationWarning]:
        """Check for LIMIT clause to prevent unbounded queries"""
        warnings = []
        sql_upper = sql.upper()

        # Check for LIMIT (PostgreSQL, MySQL) or TOP (SQL Server)
        has_limit = 'LIMIT' in sql_upper or 'TOP' in sql_upper

        if not has_limit:
            suggestion = "Add LIMIT clause to prevent returning excessive rows"
            if db_type.lower() == 'sqlserver':
                suggestion = "Add TOP clause to prevent returning excessive rows"

            warnings.append(ValidationWarning(
                severity="warning",
                message="Query does not include row limit",
                code="NO_LIMIT_CLAUSE",
                suggestion=suggestion
            ))

        return warnings

    def _check_table_references(
        self,
        sql: str,
        schema: Schema
    ) -> List[ValidationWarning]:
        """Validate that referenced tables exist in schema"""
        warnings = []

        # Get all table names from schema
        valid_tables = {table.name.lower() for table in schema.tables}

        # Extract table references from SQL (basic pattern matching)
        # This is a simplified approach - a full parser would be more accurate
        sql_lower = sql.lower()

        # Pattern: FROM table_name or JOIN table_name
        table_patterns = [
            r'\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bjoin\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        referenced_tables = set()
        for pattern in table_patterns:
            matches = re.finditer(pattern, sql_lower)
            for match in matches:
                table_name = match.group(1).lower()
                referenced_tables.add(table_name)

        # Check if referenced tables exist
        for table_name in referenced_tables:
            if table_name not in valid_tables:
                warnings.append(ValidationWarning(
                    severity="warning",
                    message=f"Table '{table_name}' not found in schema",
                    code="UNKNOWN_TABLE",
                    suggestion=f"Available tables: {', '.join(sorted(valid_tables))}"
                ))

        return warnings

    def _check_column_references(
        self,
        sql: str,
        schema: Schema
    ) -> List[ValidationWarning]:
        """Validate that referenced columns exist (basic check)"""
        warnings = []

        # Build a set of all valid column names across all tables
        # Note: This is a simplified check - ideally we'd validate columns per table
        valid_columns = set()
        for table in schema.tables:
            for column in table.columns:
                valid_columns.add(column.name.lower())

        # Extract potential column names from SELECT clause
        # Pattern: SELECT col1, col2, ... FROM
        select_match = re.search(
            r'select\s+(.*?)\s+from',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if select_match and select_match.group(1).strip() != '*':
            columns_str = select_match.group(1)

            # Parse column names (basic - doesn't handle complex expressions)
            columns = re.findall(
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b',
                columns_str
            )

            for col in columns:
                col_lower = col.lower()
                # Skip SQL keywords and functions
                if col_lower not in {
                    'count', 'sum', 'avg', 'min', 'max',
                    'distinct', 'as', 'case', 'when', 'then', 'else', 'end'
                } and col_lower not in valid_columns:
                    # This is a soft warning since our parsing is basic
                    warnings.append(ValidationWarning(
                        severity="info",
                        message=f"Column '{col}' may not exist in schema",
                        code="UNKNOWN_COLUMN",
                        suggestion="Verify column name is correct"
                    ))

        return warnings

    def _check_best_practices(
        self,
        sql: str,
        parsed: Optional[Statement]
    ) -> List[ValidationWarning]:
        """Check for SQL best practices"""
        warnings = []

        # Check for SELECT *
        if re.search(r'\bselect\s+\*\s+from', sql, re.IGNORECASE):
            warnings.append(ValidationWarning(
                severity="info",
                message="SELECT * used - consider specifying columns explicitly",
                code="SELECT_STAR",
                suggestion="Explicitly list columns for better performance and clarity"
            ))

        # Check for missing WHERE clause in queries with JOIN
        if re.search(r'\bjoin\b', sql, re.IGNORECASE):
            if not re.search(r'\bwhere\b', sql, re.IGNORECASE):
                warnings.append(ValidationWarning(
                    severity="info",
                    message="JOIN without WHERE clause",
                    code="JOIN_NO_WHERE",
                    suggestion="Consider adding WHERE clause to filter results"
                ))

        # Check SQL length (very long queries might be overly complex)
        if len(sql) > 2000:
            warnings.append(ValidationWarning(
                severity="info",
                message="Query is very long - consider simplifying",
                code="LONG_QUERY",
                suggestion="Break down complex queries into simpler parts"
            ))

        return warnings

    def is_valid(self, warnings: List[ValidationWarning]) -> bool:
        """
        Check if SQL is valid (no errors, warnings are acceptable)

        Args:
            warnings: List of validation warnings

        Returns:
            True if no errors found, False otherwise
        """
        return not any(w.severity == "error" for w in warnings)

    def get_error_messages(self, warnings: List[ValidationWarning]) -> List[str]:
        """Extract error messages from warnings"""
        return [w.message for w in warnings if w.severity == "error"]

    def get_warning_messages(self, warnings: List[ValidationWarning]) -> List[str]:
        """Extract warning messages from warnings"""
        return [w.message for w in warnings if w.severity == "warning"]
