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
    # Note: comment patterns are intentionally absent — comments are stripped
    # before these checks run, so they can never appear here. Keeping them
    # would cause every legitimate SQL comment to be flagged as injection.
    INJECTION_PATTERNS = [
        r';\s*DROP',              # Statement chaining
        r'UNION\s+SELECT',        # Union-based injection
        r'OR\s+1\s*=\s*1',        # Always-true conditions
        r'OR\s+\'1\'\s*=\s*\'1\'',
        r'SLEEP\s*\(',            # Time-based injection
        r'BENCHMARK\s*\(',
        r'WAITFOR\s+DELAY',
    ]

    def __init__(self):
        self.logger = logger.bind(service="sql_validator")

    def _strip_comments(self, sql: str) -> str:
        """Remove SQL comments, replacing each with a space to preserve token boundaries.

        This must run before all security checks so that patterns like
        ``SELECT * -- DROP TABLE users`` or ``SELECT * /* DROP */ FROM t``
        cannot hide forbidden keywords inside comments.
        """
        result = []
        for statement in sqlparse.parse(sql):
            for token in statement.flatten():
                if token.ttype in (
                    sqlparse.tokens.Comment.Single,
                    sqlparse.tokens.Comment.Multiline,
                ):
                    result.append(' ')
                else:
                    result.append(token.value)
        return ''.join(result)

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

        # Strip comments before any security check so hidden keywords can't bypass detection.
        # e.g.  SELECT * -- DROP TABLE users
        #        SELECT * /* ALTER TABLE t ... */ FROM t
        clean_sql = self._strip_comments(sql)

        # Run all validation checks on comment-free SQL
        warnings.extend(self._check_forbidden_keywords(clean_sql))
        warnings.extend(self._check_injection_patterns(clean_sql))
        warnings.extend(self._check_limit_clause(clean_sql, db_type))

        if schema:
            warnings.extend(self._check_table_references(clean_sql, schema))
            warnings.extend(self._check_column_references(clean_sql, schema))

        warnings.extend(self._check_best_practices(clean_sql, parsed[0] if parsed else None))

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

        valid_tables = {table.name.lower() for table in schema.tables}
        sql_lower = sql.lower()

        # Collect CTE names so they are not flagged as unknown tables.
        # Handles: WITH name AS (...) and the comma-separated continuations
        # WITH a AS (...), b AS (...)
        cte_names: set = set(re.findall(
            r'\bwith\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(', sql_lower
        ))
        cte_names.update(re.findall(
            r',\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(', sql_lower
        ))

        # Match FROM/JOIN with an optional schema qualifier.
        # The non-capturing group (?:schema.) is consumed but only the table
        # name after the dot (or the bare name when no dot is present) is captured.
        # Examples that now work correctly:
        #   FROM users           -> "users"
        #   FROM public.users    -> "users"   (was "public" before)
        #   FROM users u         -> "users"   (alias ignored, unchanged)
        #   FROM (SELECT ...)    -> no match  (( is not [a-zA-Z_])
        table_patterns = [
            r'\bfrom\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bjoin\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        referenced_tables: set = set()
        for pattern in table_patterns:
            for match in re.finditer(pattern, sql_lower):
                referenced_tables.add(match.group(1).lower())

        # Skip names that are CTEs or SQL keywords that can follow FROM/JOIN
        skip = cte_names | {'select', 'lateral'}

        for table_name in referenced_tables:
            if table_name in skip:
                continue
            if table_name not in valid_tables:
                warnings.append(ValidationWarning(
                    severity="warning",
                    message=f"Table '{table_name}' not found in schema",
                    code="UNKNOWN_TABLE",
                    suggestion=f"Available tables: {', '.join(sorted(valid_tables))}"
                ))

        return warnings

    # SQL keywords and built-in functions that are never column names.
    # This list is used by _check_column_references to reduce false positives.
    _COLUMN_CHECK_SKIP_WORDS: Set[str] = {
        # Structural keywords
        'select', 'from', 'where', 'join', 'inner', 'left', 'right', 'full',
        'outer', 'cross', 'on', 'and', 'or', 'not', 'in', 'between', 'like',
        'ilike', 'is', 'null', 'true', 'false', 'as', 'by', 'order', 'group',
        'having', 'limit', 'offset', 'union', 'all', 'distinct', 'case', 'when',
        'then', 'else', 'end', 'asc', 'desc', 'with', 'over', 'partition',
        'rows', 'range', 'unbounded', 'preceding', 'following', 'current', 'row',
        'exists', 'any', 'some', 'lateral', 'filter', 'within', 'interval',
        'recursive', 'window', 'returning', 'using', 'natural', 'values', 'set',
        # Aggregates and window functions
        'count', 'sum', 'avg', 'min', 'max', 'stddev', 'variance',
        'first_value', 'last_value', 'nth_value', 'lead', 'lag',
        'rank', 'dense_rank', 'row_number', 'ntile', 'percent_rank', 'cume_dist',
        'string_agg', 'array_agg', 'json_agg', 'jsonb_agg', 'bit_and', 'bit_or',
        # String functions
        'lower', 'upper', 'length', 'char_length', 'trim', 'ltrim', 'rtrim',
        'substr', 'substring', 'replace', 'concat', 'coalesce', 'nullif',
        'split_part', 'regexp_replace', 'to_char', 'initcap', 'lpad', 'rpad',
        'reverse', 'repeat', 'position', 'strpos', 'overlay', 'format',
        # Numeric / math
        'abs', 'ceil', 'ceiling', 'floor', 'round', 'trunc', 'mod', 'power',
        'sqrt', 'exp', 'ln', 'log', 'sign', 'random', 'greatest', 'least',
        # Date / time
        'now', 'current_date', 'current_time', 'current_timestamp', 'localtime',
        'localtimestamp', 'date', 'time', 'timestamp', 'extract', 'date_part',
        'date_trunc', 'age', 'to_timestamp', 'to_date', 'make_date', 'year',
        'month', 'day', 'hour', 'minute', 'second', 'epoch',
        # Type names / CAST targets
        'cast', 'convert', 'int', 'integer', 'bigint', 'smallint', 'float',
        'double', 'numeric', 'decimal', 'boolean', 'text', 'varchar', 'char',
        'bytea', 'uuid', 'json', 'jsonb', 'array', 'precision', 'value',
        # Conditional helpers
        'if', 'ifnull', 'isnull', 'nvl', 'decode', 'iif',
    }

    def _check_column_references(
        self,
        sql: str,
        schema: Schema
    ) -> List[ValidationWarning]:
        """Check column names across all clauses (SELECT, WHERE, ON, GROUP BY, ORDER BY).

        Warnings are severity "info" because regex-based extraction is inherently
        heuristic and can produce false positives on complex expressions.
        """
        warnings = []

        # Build pool of valid column names (union across all tables)
        valid_columns = set()
        for table in schema.tables:
            for column in table.columns:
                valid_columns.add(column.name.lower())

        if not valid_columns:
            return warnings

        sql_lower = sql.lower()

        # Table names are identifiers but not column references
        table_names = {table.name.lower() for table in schema.tables}

        # CTE names defined in this query are not column references
        cte_names: Set[str] = set(re.findall(
            r'\bwith\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(', sql_lower
        ))
        cte_names.update(re.findall(
            r',\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(', sql_lower
        ))

        # Column/table aliases introduced with AS are not column references
        alias_names: Set[str] = set(re.findall(
            r'\bas\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', sql_lower
        ))

        skip = self._COLUMN_CHECK_SKIP_WORDS | table_names | cte_names | alias_names

        # Strip table/alias qualifiers so "u.user_id" becomes "user_id"
        # and "u" is no longer treated as a candidate column name.
        clean = re.sub(
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\.([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\1',
            sql_lower,
        )

        # Extract every identifier token from the full SQL (covers SELECT, WHERE,
        # ON, GROUP BY, ORDER BY, HAVING — not just the SELECT list).
        all_identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', clean)
        candidates = {name for name in all_identifiers if name not in skip}

        for col in sorted(candidates):
            if col not in valid_columns:
                warnings.append(ValidationWarning(
                    severity="info",
                    message=f"Column '{col}' may not exist in schema",
                    code="UNKNOWN_COLUMN",
                    suggestion="Verify column name is correct",
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
