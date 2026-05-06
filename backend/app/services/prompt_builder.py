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
        include_descriptions: bool = True,
        max_cols_per_table: Optional[int] = None,
    ) -> str:
        """Part 2: Build enriched schema context.

        Args:
            schema: Schema ORM object with tables and columns
            include_descriptions: Include AI-generated / user-edited descriptions
            max_cols_per_table: When set, keep only the top-N most important
                columns per table (PKs first, then FKs, then NOT NULL, then
                nullable). A truncation notice is appended for omitted columns.
        """
        context_parts = []

        context_parts.append("# DATABASE SCHEMA")
        context_parts.append(f"Database: {schema.name}")
        context_parts.append(f"Type: {schema.db_type.value.upper()}")

        if include_descriptions and schema.enriched_description:
            context_parts.append(f"\n{schema.enriched_description}")

        context_parts.append("\n## Tables and Columns:\n")

        for table in schema.tables:
            # Table header with optional description
            table_header = f"### {table.name}"
            if include_descriptions and table.enriched_description:
                table_header += f"\n{table.enriched_description}"
            context_parts.append(table_header)

            # Select which columns to include
            cols = list(table.columns)
            skipped = 0
            if max_cols_per_table is not None and len(cols) > max_cols_per_table:
                cols = sorted(cols, key=self._column_priority)[:max_cols_per_table]
                skipped = len(table.columns) - max_cols_per_table

            context_parts.append("```")
            for col in cols:
                context_parts.append(self._format_column(col, include_descriptions))
            if skipped:
                context_parts.append(f"-- ... {skipped} additional column(s) omitted")
            context_parts.append("```\n")

        # FK relationship map for JOIN planning
        rel_section = self._build_relationships_section(schema)
        if rel_section:
            context_parts.append(rel_section)

        return "\n".join(context_parts)

    def _build_relationships_section(self, schema: Schema) -> str:
        """
        Build a consolidated FK → reference map for JOIN planning.

        Listing all foreign keys together in one section lets the AI plan JOIN
        chains without having to re-scan individual column annotations. For a
        multi-table query the AI can see the full graph at a glance.

        Example output:
            ## Join Relationships:
              orders.customer_id → customers.id
              order_items.order_id → orders.id
              order_items.product_id → products.id
              products.category_id → categories.id

        Returns an empty string when the schema has no foreign keys.
        """
        lines: List[str] = []
        for table in schema.tables:
            for col in table.columns:
                if col.is_foreign_key and col.foreign_key_table:
                    ref_col = col.foreign_key_column or "id"
                    lines.append(
                        f"  {table.name}.{col.name} → {col.foreign_key_table}.{ref_col}"
                    )

        if not lines:
            return ""

        return "## Join Relationships:\n" + "\n".join(lines)

    @staticmethod
    def _column_priority(col) -> int:
        """Sort key for column importance — lower = keep first when truncating.

        Order: primary keys → foreign keys → required (NOT NULL) → nullable.
        """
        if col.is_primary_key:
            return 0
        if col.is_foreign_key:
            return 1
        if not col.is_nullable:
            return 2
        return 3

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
- ❌ No multiple statements separated by ;

## Best Practices:
- ✅ Select specific columns instead of SELECT *
- ✅ Use meaningful aliases for readability
- ✅ Optimize JOINs (use appropriate JOIN type)
- ✅ Handle NULL values appropriately
- ✅ Use CTEs (WITH clauses) for multi-step logic — clearer than deeply nested subqueries
- ✅ Subqueries in WHERE / FROM are fine when they simplify the query"""

        # Add database-specific rules
        if self.db_type == "postgresql":
            rules += """

## PostgreSQL Specifics:
- **CRITICAL: Always wrap every table name and column name in double quotes** to preserve exact case (e.g., SELECT "id", "createdAt", "shopId" FROM "User" — never SELECT id, createdAt FROM User)
- This is required because Prisma/ORM schemas use PascalCase tables and camelCase columns; unquoted identifiers are folded to lowercase by PostgreSQL and will cause "column does not exist" or "relation does not exist" errors
- Use ILIKE for case-insensitive string matching
- Use :: for type casting (e.g., "column"::DATE)
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

    def _build_truncated_prompt(
        self,
        schema: Schema,
        natural_language_query: str,
        max_cols_per_table: int,
        include_descriptions: bool,
    ) -> str:
        """Build a prompt with columns truncated to the top-N most important
        per table (no examples included — examples were already dropped at an
        earlier fallback level).
        """
        parts = [
            self._build_role_context(),
            self._build_schema_context(
                schema,
                include_descriptions=include_descriptions,
                max_cols_per_table=max_cols_per_table,
            ),
            self._build_rules_and_constraints(),
            self._build_query_input(natural_language_query),
        ]
        return "\n\n".join(parts)

    def optimize_prompt_length(
        self,
        schema: Schema,
        natural_language_query: str,
        max_tokens: int = 4000,
        examples: Optional[List[Example]] = None,
    ) -> str:
        """
        Build the best possible prompt within the token budget.

        Degradation order (quality → compactness):

        1. Full context  — descriptions + few-shot examples  (best accuracy)
        2. No examples   — descriptions kept                  (descriptions > examples)
        3. Trunc cols    — top-10 columns/table + descriptions
        4. Trunc cols    — top-10 columns/table, no descriptions
        5. Minimal       — table names and column types only   (last resort)

        Args:
            schema: Schema ORM object
            natural_language_query: User's question
            max_tokens: Hard token budget (estimate, ~4 chars/token)
            examples: Optional few-shot examples

        Returns:
            The longest prompt that fits within max_tokens.
        """
        def fits(prompt: str) -> bool:
            return self.estimate_token_count(prompt) <= max_tokens

        # Level 1 — full context
        prompt = self.build_sql_generation_prompt(
            schema=schema,
            natural_language_query=natural_language_query,
            examples=examples,
            include_schema_descriptions=True,
        )
        if fits(prompt):
            return prompt

        # Level 2 — drop examples, keep descriptions
        # Descriptions carry more SQL-generation signal than few-shot examples.
        self.logger.info(
            "Prompt over budget — dropping examples, keeping descriptions",
            budget=max_tokens,
            actual=self.estimate_token_count(prompt),
        )
        prompt = self.build_sql_generation_prompt(
            schema=schema,
            natural_language_query=natural_language_query,
            examples=None,
            include_schema_descriptions=True,
        )
        if fits(prompt):
            return prompt

        # Level 3 — truncate columns (top 10 by importance), keep descriptions
        self.logger.info("Still over budget — truncating columns, keeping descriptions")
        prompt = self._build_truncated_prompt(
            schema, natural_language_query,
            max_cols_per_table=10,
            include_descriptions=True,
        )
        if fits(prompt):
            return prompt

        # Level 4 — truncate columns (top 10), drop descriptions
        self.logger.info("Still over budget — truncating columns, dropping descriptions")
        prompt = self._build_truncated_prompt(
            schema, natural_language_query,
            max_cols_per_table=10,
            include_descriptions=False,
        )
        if fits(prompt):
            return prompt

        # Level 5 — minimal context (last resort)
        self.logger.warning("Prompt still over budget — using minimal context")
        return self._build_minimal_prompt(schema, natural_language_query)

    def _build_minimal_prompt(self, schema: Schema, query: str) -> str:
        """Build minimal prompt for very large schemas"""
        minimal_schema = self.build_schema_only_context(schema)

        return f"""You are a {self.db_type.upper()} SQL expert.

{minimal_schema}

Convert to SQL (no explanations):
"{query}"

SQL:"""
