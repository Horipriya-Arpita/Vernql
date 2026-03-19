"""
Prompt Builder Service
Constructs structured prompts for SQL generation using 5-part framework

The 5-Part Prompt Structure:
1. Role & Context - Define AI's role and task
2. Schema Context - Provide database schema with enrichments
3. Examples - Show example queries (optional)
4. Rules & Constraints - Define strict requirements
5. Query Input - The actual natural language query
"""
from typing import List, Dict, Optional
import structlog

from app.models import Schema
from app.core.config import settings

logger = structlog.get_logger()


class Example:
    """Example query for few-shot learning"""

    def __init__(
        self,
        natural_language: str,
        sql: str,
        explanation: Optional[str] = None
    ):
        self.natural_language = natural_language
        self.sql = sql
        self.explanation = explanation


class PromptBuilder:
    """
    Builds structured prompts for SQL generation

    Uses a 5-part framework for optimal AI performance:
    1. Role & Context
    2. Schema Context
    3. Examples (few-shot learning)
    4. Rules & Constraints
    5. Query Input
    """

    def __init__(self, db_type: str = "postgresql"):
        """
        Initialize prompt builder

        Args:
            db_type: Database type (postgresql, mysql, sqlserver, etc.)
        """
        self.db_type = db_type.lower()
        self.logger = logger.bind(service="prompt_builder")

    def build_sql_generation_prompt(
        self,
        schema: Schema,
        natural_language_query: str,
        examples: Optional[List[Example]] = None,
        include_schema_descriptions: bool = True
    ) -> str:
        """
        Build complete SQL generation prompt using 5-part structure

        Args:
            schema: Schema object with tables and columns
            natural_language_query: User's natural language query
            examples: Optional list of example queries for few-shot learning
            include_schema_descriptions: Include AI-generated descriptions

        Returns:
            Complete prompt string
        """
        parts = []

        # Part 1: Role & Context
        parts.append(self._build_role_context())

        # Part 2: Schema Context
        schema_context = self._build_schema_context(
            schema,
            include_descriptions=include_schema_descriptions
        )
        parts.append(schema_context)

        # Part 3: Examples (if provided)
        if examples:
            examples_section = self._build_examples_section(examples)
            parts.append(examples_section)

        # Part 4: Rules & Constraints
        rules = self._build_rules_and_constraints()
        parts.append(rules)

        # Part 5: Query Input
        query_input = self._build_query_input(natural_language_query)
        parts.append(query_input)

        # Combine all parts
        prompt = "\n\n".join(parts)

        self.logger.debug(
            "Prompt built",
            db_type=self.db_type,
            has_examples=bool(examples),
            prompt_length=len(prompt)
        )

        return prompt

    def _build_role_context(self) -> str:
        """Part 1: Define AI's role and context"""
        db_name = self.db_type.upper()

        return f"""You are an expert {db_name} database developer specializing in converting natural language queries into optimized SQL.

Your task is to generate a single, valid {db_name} SQL query that accurately answers the user's question based on the provided database schema."""

    def _build_schema_context(
        self,
        schema: Schema,
        include_descriptions: bool = True
    ) -> str:
        """Part 2: Build enriched schema context"""
        context_parts = []

        context_parts.append("# DATABASE SCHEMA")
        context_parts.append(f"Database: {schema.name}")
        context_parts.append(f"Type: {schema.db_type.value.upper()}")

        if include_descriptions and schema.enriched_description:
            context_parts.append(f"\n{schema.enriched_description}")

        context_parts.append("\n## Tables and Columns:\n")

        # Build table information
        for table in schema.tables:
            # Table header
            table_header = f"### {table.name}"
            if include_descriptions and table.enriched_description:
                table_header += f"\n{table.enriched_description}"
            context_parts.append(table_header)

            # Columns
            context_parts.append("```")
            for col in table.columns:
                col_line = self._format_column(col, include_descriptions)
                context_parts.append(col_line)
            context_parts.append("```\n")

        return "\n".join(context_parts)

    def _format_column(self, column, include_descriptions: bool = True) -> str:
        """Format a single column with metadata"""
        # Build column type and constraints
        parts = [column.name, column.data_type]

        constraints = []
        if column.is_primary_key:
            constraints.append("PRIMARY KEY")
        if column.is_foreign_key:
            constraints.append(f"FK → {column.foreign_key_table}.{column.foreign_key_column or 'id'}")
        if not column.is_nullable:
            constraints.append("NOT NULL")

        if constraints:
            parts.append(f"[{', '.join(constraints)}]")

        # Add description if available
        if include_descriptions and column.enriched_description:
            parts.append(f"-- {column.enriched_description}")

        return " ".join(parts)

    def _build_examples_section(self, examples: List[Example]) -> str:
        """Part 3: Build examples section for few-shot learning"""
        if not examples:
            return ""

        parts = ["# EXAMPLES", "\nHere are examples of correct query conversions:\n"]

        for i, example in enumerate(examples, 1):
            parts.append(f"## Example {i}")
            parts.append(f"Question: {example.natural_language}")
            parts.append(f"SQL:\n```sql\n{example.sql}\n```")

            if example.explanation:
                parts.append(f"Explanation: {example.explanation}")

            parts.append("")  # Empty line between examples

        return "\n".join(parts)

    def _build_rules_and_constraints(self) -> str:
        """Part 4: Define strict rules and constraints"""
        db_name = self.db_type.upper()

        rules = f"""# RULES AND REQUIREMENTS

## Output Format:
- Return ONLY the SQL query
- No explanations, markdown formatting, or additional text
- Do not wrap in ```sql code blocks
- End with semicolon

## SQL Requirements:
1. **Syntax**: Use proper {db_name} syntax and functions
2. **Table/Column Names**: Use EXACT names from schema (case-sensitive)
3. **LIMIT Clause**: Always include LIMIT {settings.SQL_DEFAULT_LIMIT} unless user specifies a number
4. **JOINs**: Use explicit JOIN syntax (INNER JOIN, LEFT JOIN) with ON conditions
5. **WHERE Clauses**: Add appropriate filters based on the question
6. **ORDER BY**: Include when query asks for "top", "recent", "best", or sorted results
7. **Aggregations**: Use GROUP BY with aggregate functions (COUNT, SUM, AVG, MIN, MAX)
8. **String Literals**: Use single quotes for strings in {db_name}
9. **Date/Time**: Use proper {db_name} date functions and formats

## Prohibited Operations:
- ❌ No DROP, DELETE, TRUNCATE, ALTER, CREATE, INSERT, UPDATE
- ❌ No EXEC, EXECUTE, or dynamic SQL
- ❌ No comments (-- or /* */)
- ❌ No multiple statements (;)
- ❌ No subqueries unless absolutely necessary

## Best Practices:
- ✅ Select specific columns instead of SELECT *
- ✅ Use meaningful aliases for readability
- ✅ Optimize JOINs (use appropriate type)
- ✅ Add indexes hints if available
- ✅ Handle NULL values appropriately"""

        # Add database-specific rules
        if self.db_type == "postgresql":
            rules += """

## PostgreSQL Specifics:
- Use ILIKE for case-insensitive string matching
- Use :: for type casting (e.g., column::DATE)
- Use EXTRACT() for date parts
- String concatenation with ||"""

        elif self.db_type == "mysql":
            rules += """

## MySQL Specifics:
- Use LIKE for string matching
- Use CAST() or CONVERT() for type conversion
- Use DATE_FORMAT() for date formatting
- String concatenation with CONCAT()"""

        elif self.db_type == "sqlserver":
            rules += """

## SQL Server Specifics:
- Use TOP instead of LIMIT
- Use CAST() or CONVERT() for type conversion
- Use DATEPART() for date parts
- String concatenation with +"""

        return rules

    def _build_query_input(self, natural_language_query: str) -> str:
        """Part 5: Format the actual query input"""
        return f"""# USER QUERY

Convert this question to SQL:

"{natural_language_query}"

SQL:"""

    def build_schema_only_context(self, schema: Schema) -> str:
        """
        Build lightweight schema context (tables and columns only)
        Useful for token-constrained scenarios

        Args:
            schema: Schema object

        Returns:
            Minimal schema representation
        """
        parts = [f"Database: {schema.name} ({schema.db_type.value})"]

        for table in schema.tables:
            columns = [f"{col.name}:{col.data_type}" for col in table.columns]
            parts.append(f"{table.name} ({', '.join(columns)})")

        return "\n".join(parts)

    def estimate_token_count(self, prompt: str) -> int:
        """
        Estimate token count for prompt (rough approximation)

        Args:
            prompt: Prompt string

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(prompt) // 4

    def optimize_prompt_length(
        self,
        schema: Schema,
        natural_language_query: str,
        max_tokens: int = 4000
    ) -> str:
        """
        Build prompt optimized for token limit

        Args:
            schema: Schema object
            natural_language_query: User query
            max_tokens: Maximum token limit

        Returns:
            Optimized prompt
        """
        # Try full prompt first
        full_prompt = self.build_sql_generation_prompt(
            schema=schema,
            natural_language_query=natural_language_query,
            include_schema_descriptions=True
        )

        if self.estimate_token_count(full_prompt) <= max_tokens:
            return full_prompt

        # If too long, try without descriptions
        self.logger.info("Prompt too long, removing descriptions")
        no_desc_prompt = self.build_sql_generation_prompt(
            schema=schema,
            natural_language_query=natural_language_query,
            include_schema_descriptions=False
        )

        if self.estimate_token_count(no_desc_prompt) <= max_tokens:
            return no_desc_prompt

        # If still too long, use minimal context
        self.logger.warning("Prompt still too long, using minimal context")
        return self._build_minimal_prompt(schema, natural_language_query)

    def _build_minimal_prompt(self, schema: Schema, query: str) -> str:
        """Build minimal prompt for very large schemas"""
        minimal_schema = self.build_schema_only_context(schema)

        return f"""You are a {self.db_type.upper()} SQL expert.

{minimal_schema}

Convert to SQL (no explanations):
"{query}"

SQL:"""
