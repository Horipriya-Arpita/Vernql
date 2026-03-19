"""
SQL Generator Service
Converts natural language queries to SQL using AI and enriched schema

Refactored to use modular components:
- SQLValidator for validation
- PromptBuilder for structured prompts
- ExampleManager for few-shot learning
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import sqlparse
import re
import structlog

from app.services.ai_provider import AIProviderFactory, BaseAIProvider
from app.services.sql_validator import SQLValidator, ValidationWarning
from app.services.prompt_builder import PromptBuilder
from app.services.example_manager import ExampleManager
from app.models import Schema, SchemaTable, SchemaColumn, Query, QueryStatus
from app.core.config import settings

logger = structlog.get_logger()


class SQLGenerationResult:
    """Result from SQL generation"""

    def __init__(
        self,
        sql: str,
        confidence: float,
        explanation: Optional[str] = None,
        warnings: Optional[List[str]] = None
    ):
        self.sql = sql
        self.confidence = confidence
        self.explanation = explanation
        self.warnings = warnings or []


class SQLGenerator:
    """
    Service for generating SQL from natural language queries

    Uses modular architecture with:
    - SQLValidator for security and validation
    - PromptBuilder for structured prompt generation
    - ExampleManager for few-shot learning
    """

    def __init__(
        self,
        ai_provider: Optional[BaseAIProvider] = None,
        use_examples: bool = True
    ):
        """
        Initialize SQL generator

        Args:
            ai_provider: Optional AI provider (uses settings default if not provided)
            use_examples: Whether to use example-based learning
        """
        self.ai_provider = ai_provider or AIProviderFactory.create_from_settings()
        self.validator = SQLValidator()
        self.example_manager = ExampleManager()
        self.use_examples = use_examples
        self.logger = logger.bind(service="sql_generator")

    async def generate_sql(
        self,
        db: Session,
        schema_id: str,
        natural_language_query: str,
        company_id: str
    ) -> SQLGenerationResult:
        """
        Generate SQL from natural language query

        Args:
            db: Database session
            schema_id: UUID of the schema to query
            natural_language_query: Natural language query
            company_id: UUID of the company (for authorization)

        Returns:
            SQLGenerationResult with SQL and confidence

        Raises:
            ValueError: If schema not found or invalid
        """
        # Get schema with enriched descriptions
        schema = db.query(Schema).filter(
            Schema.id == schema_id,
            Schema.company_id == company_id,
            Schema.is_active == True
        ).first()

        if not schema:
            raise ValueError(f"Schema {schema_id} not found or inaccessible")

        self.logger.info(
            "Generating SQL",
            schema=schema.name,
            query_preview=natural_language_query[:100]
        )

        # Get relevant examples for few-shot learning
        examples = []
        if self.use_examples:
            examples = self.example_manager.find_relevant_examples(
                db=db,
                company_id=company_id,
                natural_language_query=natural_language_query,
                schema_id=schema_id,
                limit=3
            )

        # Build prompt using PromptBuilder
        prompt_builder = PromptBuilder(db_type=schema.db_type.value)
        prompt = prompt_builder.build_sql_generation_prompt(
            schema=schema,
            natural_language_query=natural_language_query,
            examples=examples,
            include_schema_descriptions=True
        )

        # Call AI
        response = await self.ai_provider.simple_completion(
            prompt=prompt,
            temperature=0.1,  # Very low for deterministic SQL
            max_tokens=1000
        )

        # Parse response
        result = self._parse_ai_response(response)

        # Validate SQL using SQLValidator
        validation_warnings = self.validator.validate(
            sql=result.sql,
            schema=schema,
            db_type=schema.db_type.value
        )

        # Convert ValidationWarning objects to strings for backward compatibility
        result.warnings = [w.message for w in validation_warnings]

        # Check if SQL has critical errors
        has_errors = not self.validator.is_valid(validation_warnings)

        # Calculate confidence
        confidence = self._calculate_confidence(
            result=result,
            schema=schema,
            query=natural_language_query,
            has_validation_errors=has_errors
        )
        result.confidence = confidence

        # Auto-create example from high-confidence queries
        if confidence >= 0.9 and not has_errors and self.use_examples:
            self.example_manager.auto_create_example_from_query(
                db=db,
                company_id=company_id,
                schema_id=schema_id,
                natural_language=natural_language_query,
                sql_query=result.sql,
                confidence_score=confidence
            )

        self.logger.info(
            "SQL generated",
            confidence=confidence,
            warnings_count=len(result.warnings),
            has_errors=has_errors,
            used_examples=len(examples)
        )

        return result

    # Note: _build_schema_context and _create_sql_generation_prompt
    # have been replaced by PromptBuilder module for better modularity

    def _parse_ai_response(self, response: str) -> SQLGenerationResult:
        """
        Parse AI response to extract SQL

        Args:
            response: Raw AI response

        Returns:
            SQLGenerationResult with parsed SQL
        """
        # Clean up response
        sql = response.strip()

        # Remove markdown code blocks if present
        if sql.startswith("```"):
            # Extract content between ```sql and ```
            match = re.search(r'```(?:sql)?\s*\n(.*?)\n```', sql, re.DOTALL)
            if match:
                sql = match.group(1).strip()
            else:
                # Just remove the ``` markers
                sql = sql.replace("```sql", "").replace("```", "").strip()

        # Remove any trailing semicolon (we'll add it when executing)
        sql = sql.rstrip(';')

        # Format SQL nicely
        try:
            sql = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper'
            )
        except Exception as e:
            self.logger.warning("SQL formatting failed", error=str(e))

        return SQLGenerationResult(
            sql=sql,
            confidence=0.0,  # Will be calculated later
            explanation=None
        )

    # Note: _validate_sql has been replaced by SQLValidator module
    # for comprehensive validation with better error reporting

    def _calculate_confidence(
        self,
        result: SQLGenerationResult,
        schema: Schema,
        query: str,
        has_validation_errors: bool = False
    ) -> float:
        """
        Calculate confidence score for generated SQL

        Args:
            result: SQL generation result
            schema: Schema object
            query: Original natural language query
            has_validation_errors: Whether validation found critical errors

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 1.0

        # Critical: validation errors drastically reduce confidence
        if has_validation_errors:
            confidence = 0.2  # Very low confidence for queries with errors
            return confidence

        # Reduce confidence for warnings (less severe than errors)
        warning_count = len(result.warnings)
        if warning_count > 0:
            confidence -= min(0.3, 0.05 * warning_count)

        # Reduce confidence if schema not enriched
        if not schema.enriched_description:
            confidence -= 0.1

        # Reduce confidence for very complex queries
        query_words = len(query.split())
        if query_words > 30:
            confidence -= 0.1

        # Reduce confidence if SQL is very short (might be incomplete)
        if len(result.sql) < 20:
            confidence -= 0.2

        # Reduce confidence if SQL is very long (might be overcomplicated)
        if len(result.sql) > 1000:
            confidence -= 0.1

        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    async def store_query_result(
        self,
        db: Session,
        company_id: str,
        schema_id: str,
        natural_language_query: str,
        generated_sql: str,
        confidence: float,
        status: QueryStatus = QueryStatus.SUCCESS,
        execution_time_ms: Optional[int] = None,
        result_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Query:
        """
        Store query result in database

        Args:
            db: Database session
            company_id: UUID of company
            schema_id: UUID of schema
            natural_language_query: Original query
            generated_sql: Generated SQL
            confidence: Confidence score
            status: Query status
            execution_time_ms: Execution time
            result_count: Number of results
            error_message: Error message if failed

        Returns:
            Query object
        """
        query = Query(
            company_id=company_id,
            schema_id=schema_id,
            natural_language_query=natural_language_query,
            generated_sql=generated_sql,
            ai_provider=self.ai_provider.get_provider_name(),
            ai_model=self.ai_provider.model,
            confidence_score=confidence,
            status=status,
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            error_message=error_message
        )

        db.add(query)
        db.commit()
        db.refresh(query)

        return query
