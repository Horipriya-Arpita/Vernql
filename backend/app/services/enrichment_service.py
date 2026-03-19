"""
Schema Enrichment Service
Uses AI to generate human-friendly descriptions for database schemas
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import structlog
import json

from app.services.ai_provider import AIProviderFactory, BaseAIProvider
from app.models import Schema, SchemaTable, SchemaColumn

logger = structlog.get_logger()


class EnrichmentService:
    """Service for enriching database schemas with AI-generated descriptions"""

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        """
        Initialize enrichment service

        Args:
            ai_provider: Optional AI provider (uses settings default if not provided)
        """
        self.ai_provider = ai_provider or AIProviderFactory.create_from_settings()
        self.logger = logger.bind(service="enrichment")

    async def enrich_schema(
        self,
        db: Session,
        schema_id: str
    ) -> Schema:
        """
        Enrich an entire schema with AI-generated descriptions

        Args:
            db: Database session
            schema_id: UUID of the schema to enrich

        Returns:
            Enriched schema object
        """
        # Get schema with tables and columns
        schema = db.query(Schema).filter(Schema.id == schema_id).first()

        if not schema:
            raise ValueError(f"Schema {schema_id} not found")

        self.logger.info(
            "Starting schema enrichment",
            schema_id=schema_id,
            schema_name=schema.name,
            tables=len(schema.tables)
        )

        # Enrich schema overview
        schema_desc = await self._generate_schema_description(schema)
        schema.enriched_description = schema_desc

        # Enrich each table
        for table in schema.tables:
            try:
                # Generate table description
                table_desc = await self._generate_table_description(
                    schema_name=schema.name,
                    table=table
                )
                table.enriched_description = table_desc

                # Enrich columns
                for column in table.columns:
                    col_desc = await self._generate_column_description(
                        table_name=table.name,
                        column=column,
                        sample_data=table.sample_values
                    )
                    column.enriched_description = col_desc

                self.logger.info(
                    "Enriched table",
                    table=table.name,
                    columns=len(table.columns)
                )

            except Exception as e:
                self.logger.error(
                    "Failed to enrich table",
                    table=table.name,
                    error=str(e)
                )
                # Continue with other tables

        # Update enrichment timestamp
        schema.enriched_at = datetime.now(timezone.utc)

        # Commit changes
        db.commit()
        db.refresh(schema)

        self.logger.info(
            "Schema enrichment complete",
            schema_id=schema_id,
            tables_enriched=len(schema.tables)
        )

        return schema

    async def _generate_schema_description(self, schema: Schema) -> str:
        """Generate overall schema description"""

        # Build table summary
        table_summary = []
        for table in schema.tables:
            col_count = len(table.columns)
            row_count = ""
            if table.sample_values and isinstance(table.sample_values, dict):
                rc = table.sample_values.get('row_count')
                if rc:
                    row_count = f" ({rc:,} rows)"

            table_summary.append(f"- {table.name}: {col_count} columns{row_count}")

        tables_text = "\n".join(table_summary)

        prompt = f"""Analyze this database schema and provide a concise, business-focused description.

Database: {schema.name}
Type: {schema.db_type.value}
Tables ({len(schema.tables)}):
{tables_text}

Provide a 1-2 sentence description that explains:
1. The primary purpose/domain of this database
2. What kind of data it manages

Be specific and informative. Don't use generic phrases like "this database stores information" - explain WHAT information and WHY.

Description:"""

        description = await self.ai_provider.simple_completion(
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistency
            max_tokens=150
        )

        return description.strip()

    async def _generate_table_description(
        self,
        schema_name: str,
        table: SchemaTable
    ) -> str:
        """Generate description for a table"""

        # Build column list
        column_list = []
        for col in table.columns:
            flags = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_foreign_key:
                flags.append(f"FK->{col.foreign_key_table}")

            flag_str = f" [{', '.join(flags)}]" if flags else ""
            column_list.append(f"- {col.name} ({col.data_type}){flag_str}")

        columns_text = "\n".join(column_list[:15])  # Limit to first 15 columns

        if len(table.columns) > 15:
            columns_text += f"\n... and {len(table.columns) - 15} more columns"

        prompt = f"""Analyze this database table and provide a clear, specific description.

Schema: {schema_name}
Table: {table.name}
Columns ({len(table.columns)}):
{columns_text}

Provide a 1-2 sentence description that explains:
1. What business entity or concept this table represents
2. Its primary purpose in the database

Be specific about the business domain. Use singular form (e.g., "A customer record" not "Customer records").

Description:"""

        description = await self.ai_provider.simple_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=100
        )

        return description.strip()

    async def _generate_column_description(
        self,
        table_name: str,
        column: SchemaColumn,
        sample_data: Optional[dict] = None
    ) -> str:
        """Generate description for a column"""

        # Extract sample values if available
        sample_values_text = ""
        if sample_data and isinstance(sample_data, dict):
            sample_rows = sample_data.get('sample_rows', [])
            if sample_rows and column.name in sample_rows[0]:
                values = [str(row.get(column.name))[:50] for row in sample_rows[:3]]
                sample_values_text = f"\nSample values: {', '.join(values)}"

        # Build context
        flags = []
        if column.is_primary_key:
            flags.append("Primary Key")
        if column.is_foreign_key:
            flags.append(f"Foreign Key to {column.foreign_key_table}.{column.foreign_key_column}")
        if not column.is_nullable:
            flags.append("Required")

        flags_text = f"\nProperties: {', '.join(flags)}" if flags else ""

        prompt = f"""Describe this database column clearly and concisely.

Table: {table_name}
Column: {column.name}
Type: {column.data_type}{flags_text}{sample_values_text}

Provide a SHORT (5-10 words) description explaining what this column stores.
Focus on BUSINESS MEANING, not technical details.
Don't repeat the column name or type.

Description:"""

        description = await self.ai_provider.simple_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=50
        )

        # Clean up response
        description = description.strip()

        # Remove common prefixes
        prefixes = [
            "This column stores ",
            "This column contains ",
            "This column represents ",
            "Stores ",
            "Contains ",
            "Represents ",
            "The ",
            "A ",
        ]

        for prefix in prefixes:
            if description.startswith(prefix):
                description = description[len(prefix):]
                break

        # Ensure first letter is capitalized
        if description:
            description = description[0].upper() + description[1:]

        return description
