"""
SQL Generation Prompt Templates
Reusable prompt templates for different SQL generation scenarios
"""
from typing import Dict


class SQLPromptTemplates:
    """Collection of prompt templates for SQL generation"""

    @staticmethod
    def get_base_system_prompt(db_type: str) -> str:
        """
        Get base system prompt for SQL generation

        Args:
            db_type: Database type (postgresql, mysql, sqlserver)

        Returns:
            System prompt string
        """
        return f"""You are an expert {db_type.upper()} database developer. Your role is to convert natural language questions into accurate, optimized SQL queries.

Key Responsibilities:
- Generate syntactically correct {db_type.upper()} SQL
- Follow database best practices
- Ensure query safety and security
- Optimize for performance
- Return ONLY the SQL query, no explanations"""

    @staticmethod
    def get_schema_instruction_template() -> str:
        """Get template for schema context instruction"""
        return """Use ONLY the tables and columns defined in the schema below.
Every table name and column name must match EXACTLY as shown (including case)."""

    @staticmethod
    def get_safety_rules_template() -> str:
        """Get safety rules template"""
        return """CRITICAL SAFETY RULES:
1. ONLY generate SELECT queries
2. NEVER use: DROP, DELETE, TRUNCATE, ALTER, CREATE, INSERT, UPDATE
3. NO SQL injection patterns (comments, unions, etc.)
4. Always include LIMIT clause for safety
5. Use parameterization patterns when applicable"""

    @staticmethod
    def get_output_format_template() -> str:
        """Get output format instructions"""
        return """OUTPUT FORMAT:
- Return ONLY the SQL query
- NO markdown code blocks (```sql)
- NO explanations or comments
- End with semicolon
- Use proper formatting and indentation"""

    @staticmethod
    def get_quality_guidelines(db_type: str) -> str:
        """
        Get quality guidelines for SQL generation

        Args:
            db_type: Database type

        Returns:
            Quality guidelines string
        """
        base_guidelines = """QUALITY GUIDELINES:
- Use explicit JOIN syntax (INNER JOIN, LEFT JOIN)
- Always specify ON conditions for JOINs
- Use WHERE clauses for filtering
- Include ORDER BY when sorting is implied
- Use GROUP BY with aggregate functions
- Select specific columns (avoid SELECT *)
- Use meaningful table aliases
- Handle NULL values appropriately
- Apply proper data type conversions"""

        # Add database-specific guidelines
        db_specific = {
            "postgresql": """
- Use ILIKE for case-insensitive matching
- Use :: for type casting (e.g., value::INTEGER)
- Use EXTRACT() for date parts
- Use || for string concatenation
- Use COALESCE() for NULL handling""",

            "mysql": """
- Use LIKE for pattern matching
- Use CAST() or CONVERT() for type conversion
- Use DATE_FORMAT() for date formatting
- Use CONCAT() for string concatenation
- Use IFNULL() or COALESCE() for NULL handling""",

            "sqlserver": """
- Use TOP N instead of LIMIT
- Use CAST() or CONVERT() for type conversion
- Use DATEPART() for date components
- Use + for string concatenation
- Use ISNULL() or COALESCE() for NULL handling"""
        }

        if db_type.lower() in db_specific:
            base_guidelines += "\n\nDatabase-Specific:\n" + db_specific[db_type.lower()]

        return base_guidelines

    @staticmethod
    def get_example_template() -> str:
        """Get template for examples section"""
        return """EXAMPLES:

The following examples demonstrate correct query patterns:

{examples}

Now apply the same principles to the user's question."""

    @staticmethod
    def get_ambiguity_handling_template() -> str:
        """Get template for handling ambiguous queries"""
        return """HANDLING AMBIGUITY:
- If the question is unclear, make reasonable assumptions
- If multiple interpretations exist, choose the most common use case
- If critical information is missing, use sensible defaults
- Add appropriate WHERE clauses based on context
- Default to recent/latest data when time is ambiguous"""

    @staticmethod
    def get_common_patterns() -> Dict[str, str]:
        """
        Get common query pattern templates

        Returns:
            Dictionary of pattern name to template
        """
        return {
            "count": """-- Counting records
SELECT COUNT(*) as total
FROM {table}
WHERE {conditions};""",

            "top_n": """-- Getting top N records
SELECT {columns}
FROM {table}
ORDER BY {sort_column} DESC
LIMIT {n};""",

            "aggregation": """-- Aggregation with grouping
SELECT {group_column}, COUNT(*) as count, AVG({value_column}) as average
FROM {table}
GROUP BY {group_column}
ORDER BY count DESC;""",

            "join_simple": """-- Simple JOIN
SELECT {table1_columns}, {table2_columns}
FROM {table1}
INNER JOIN {table2} ON {table1}.{key} = {table2}.{foreign_key}
WHERE {conditions};""",

            "date_filter": """-- Date filtering
SELECT {columns}
FROM {table}
WHERE {date_column} >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY {date_column} DESC;""",

            "search": """-- Text search
SELECT {columns}
FROM {table}
WHERE {text_column} ILIKE '%{search_term}%'
LIMIT 100;"""
        }

    @staticmethod
    def build_complete_prompt(
        db_type: str,
        schema_context: str,
        user_query: str,
        examples: str = "",
        include_patterns: bool = False
    ) -> str:
        """
        Build complete prompt from templates

        Args:
            db_type: Database type
            schema_context: Formatted schema information
            user_query: User's natural language query
            examples: Optional examples section
            include_patterns: Include common patterns

        Returns:
            Complete prompt string
        """
        parts = []

        # System prompt
        parts.append(SQLPromptTemplates.get_base_system_prompt(db_type))

        # Schema context
        parts.append("=" * 60)
        parts.append("DATABASE SCHEMA")
        parts.append("=" * 60)
        parts.append(SQLPromptTemplates.get_schema_instruction_template())
        parts.append(schema_context)

        # Examples (if provided)
        if examples:
            parts.append("\n" + "=" * 60)
            parts.append(SQLPromptTemplates.get_example_template().format(examples=examples))

        # Common patterns (optional)
        if include_patterns:
            patterns = SQLPromptTemplates.get_common_patterns()
            patterns_str = "\n\n".join(patterns.values())
            parts.append("\n" + "=" * 60)
            parts.append("COMMON PATTERNS")
            parts.append("=" * 60)
            parts.append(patterns_str)

        # Rules and guidelines
        parts.append("\n" + "=" * 60)
        parts.append("RULES AND GUIDELINES")
        parts.append("=" * 60)
        parts.append(SQLPromptTemplates.get_safety_rules_template())
        parts.append("\n" + SQLPromptTemplates.get_quality_guidelines(db_type))
        parts.append("\n" + SQLPromptTemplates.get_ambiguity_handling_template())
        parts.append("\n" + SQLPromptTemplates.get_output_format_template())

        # User query
        parts.append("\n" + "=" * 60)
        parts.append("YOUR TASK")
        parts.append("=" * 60)
        parts.append(f'Convert this question to {db_type.upper()} SQL:\n\n"{user_query}"')
        parts.append("\nSQL Query:")

        return "\n\n".join(parts)


class PromptOptimizer:
    """Helper class for optimizing prompts"""

    @staticmethod
    def calculate_token_estimate(text: str) -> int:
        """
        Estimate token count (rough approximation)

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    @staticmethod
    def truncate_schema_descriptions(
        schema_context: str,
        max_tokens: int
    ) -> str:
        """
        Truncate schema descriptions to fit token limit

        Args:
            schema_context: Full schema context
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated schema context
        """
        current_tokens = PromptOptimizer.calculate_token_estimate(schema_context)

        if current_tokens <= max_tokens:
            return schema_context

        # Remove descriptions (keep only structure)
        lines = schema_context.split('\n')
        essential_lines = [
            line for line in lines
            if not line.strip().startswith('--') and
            not line.strip().startswith('#') and
            line.strip()
        ]

        return '\n'.join(essential_lines)

    @staticmethod
    def prioritize_relevant_tables(
        schema_context: str,
        user_query: str,
        max_tables: int = 10
    ) -> str:
        """
        Filter schema to most relevant tables based on query

        Args:
            schema_context: Full schema context
            user_query: User's query
            max_tables: Maximum tables to include

        Returns:
            Filtered schema context
        """
        # Simple keyword matching approach
        # In production, could use embeddings for semantic matching
        query_keywords = set(user_query.lower().split())

        # Extract table sections
        tables = schema_context.split('\n\n')

        # Score tables by keyword relevance
        scored_tables = []
        for table in tables:
            table_lower = table.lower()
            score = sum(1 for keyword in query_keywords if keyword in table_lower)
            scored_tables.append((score, table))

        # Sort by relevance and take top N
        scored_tables.sort(reverse=True, key=lambda x: x[0])
        relevant_tables = [table for _, table in scored_tables[:max_tables]]

        return '\n\n'.join(relevant_tables)
