"""
Schema Enrichment Service
Generates business-meaningful AI descriptions for database schemas.

Strategy (three-level fallback):

1. Holistic  — one AI call for the entire schema → JSON with all descriptions.
   Best quality: AI sees every table and relationship simultaneously.
   Used when schema ≤ HOLISTIC_MAX_TABLES tables and ≤ HOLISTIC_MAX_COLUMNS columns.

2. Batched   — one AI call per table, but every call receives the full schema
   overview as background context, preserving cross-table awareness.
   Used when the schema exceeds the holistic thresholds.

3. Legacy    — original per-column N+1 calls, no cross-table context.
   Used only when both upper strategies fail (e.g. malformed JSON repeatedly).
"""
import json
import re
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy.orm import Session

from app.models import Schema, SchemaColumn, SchemaTable, DescriptionSource
from app.services.ai_provider import AIProviderFactory, BaseAIProvider

logger = structlog.get_logger()

# Thresholds for the holistic single-call strategy
HOLISTIC_MAX_TABLES = 40
HOLISTIC_MAX_COLUMNS = 400


class EnrichmentService:
    """Enrich database schemas with AI-generated business descriptions."""

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None) -> None:
        self.ai_provider = ai_provider or AIProviderFactory.create_from_settings()
        self.logger = logger.bind(service="enrichment")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def enrich_schema(self, db: Session, schema_id: str) -> Schema:
        """
        Enrich an entire schema with AI-generated descriptions and persist.

        Args:
            db: Database session
            schema_id: UUID of the schema to enrich

        Returns:
            The enriched Schema ORM object (already committed)
        """
        schema = db.query(Schema).filter(Schema.id == schema_id).first()
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")

        total_columns = sum(len(t.columns) for t in schema.tables)
        self.logger.info(
            "Starting schema enrichment",
            schema_id=schema_id,
            schema_name=schema.name,
            tables=len(schema.tables),
            columns=total_columns,
        )

        use_holistic = (
            len(schema.tables) <= HOLISTIC_MAX_TABLES
            and total_columns <= HOLISTIC_MAX_COLUMNS
        )

        if use_holistic:
            await self._enrich_holistic(schema)
        else:
            await self._enrich_batched(schema)

        schema.enriched_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(schema)

        self.logger.info(
            "Schema enrichment complete",
            schema_id=schema_id,
            tables_enriched=len(schema.tables),
        )
        return schema

    # ------------------------------------------------------------------
    # Strategy 1: Holistic — single call for the entire schema
    # ------------------------------------------------------------------

    async def _enrich_holistic(self, schema: Schema) -> None:
        """
        Send the complete schema in one prompt and parse the JSON response.
        Falls back to batched if the AI returns unparseable output.
        """
        prompt = self._build_holistic_prompt(schema)
        self.logger.info("Sending holistic prompt", prompt_chars=len(prompt))

        try:
            raw = await self.ai_provider.simple_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=8000,
            )
            data = self._parse_json(raw)
            self._apply_data(schema, data)
            self.logger.info("Holistic enrichment applied")
        except Exception as exc:
            self.logger.warning(
                "Holistic enrichment failed — falling back to batched",
                error=str(exc),
            )
            await self._enrich_batched(schema)

    def _build_holistic_prompt(self, schema: Schema) -> str:
        schema_block = self._render_full_schema(schema.tables)
        rel_block = self._render_relationships(schema.tables)

        return f"""You are a database analyst. Write clear, business-focused descriptions for the database schema below.

DATABASE: {schema.name}
TYPE: {schema.db_type.value.upper()}

{schema_block}{rel_block}

Return ONLY a valid JSON object — no markdown fences, no text before or after:
{{
  "schema_description": "1-3 sentences describing the overall purpose and business domain of this database",
  "tables": {{
    "<TABLE_NAME>": {{
      "description": "1-2 sentences: what business entity/concept this table represents and its role",
      "columns": {{
        "<COLUMN_NAME>": "10-30 words: what this column stores, in business terms (not technical)"
      }}
    }}
  }}
}}

Guidelines:
- Be specific to this domain — never say "stores data" or "contains information"
- For FK columns: state the relationship (e.g. "ID of the customer who placed this order")
- Column descriptions: business meaning only, present-tense noun phrase
- Include EVERY table and EVERY column listed above

JSON:"""

    # ------------------------------------------------------------------
    # Strategy 2: Batched — one call per table, full schema as context
    # ------------------------------------------------------------------

    async def _enrich_batched(self, schema: Schema) -> None:
        """
        For schemas that exceed the holistic threshold.
        Each table gets its own call but receives the full schema as context.
        Falls back to legacy per-column calls if a table's JSON is invalid.
        """
        full_schema_ctx = self._render_full_schema(schema.tables)
        rel_ctx = self._render_relationships(schema.tables)
        background = (
            f"DATABASE: {schema.name}\n"
            f"TYPE: {schema.db_type.value.upper()}\n\n"
            f"{full_schema_ctx}{rel_ctx}"
        )

        # Schema-level description from the full context
        try:
            schema.enriched_description = await self._gen_schema_description_legacy(schema)
        except Exception as exc:
            self.logger.warning("Schema-level description failed", error=str(exc))

        for table in schema.tables:
            try:
                await self._enrich_single_table(table, schema.name, background)
            except Exception as exc:
                self.logger.error(
                    "Batched enrichment failed for table — falling back to legacy",
                    table=table.name,
                    error=str(exc),
                )
                try:
                    await self._enrich_table_legacy(schema.name, table)
                except Exception as inner_exc:
                    self.logger.error(
                        "Legacy enrichment also failed for table",
                        table=table.name,
                        error=str(inner_exc),
                    )

    async def _enrich_single_table(
        self,
        table: SchemaTable,
        schema_name: str,
        full_schema_background: str,
    ) -> None:
        """Enrich one table with the full schema visible as background context."""
        cols_lines = []
        for col in table.columns:
            fk = (
                f" [FK→{col.foreign_key_table}.{col.foreign_key_column}]"
                if col.is_foreign_key
                else ""
            )
            cols_lines.append(f"  {col.name} ({col.data_type}){fk}")

        cols_block = "\n".join(cols_lines)

        prompt = f"""You are a database analyst. Using the full schema as context, write descriptions for the table '{table.name}'.

FULL SCHEMA CONTEXT:
{full_schema_background}

FOCUS: TABLE '{table.name}'
{cols_block}

Return ONLY a valid JSON object:
{{
  "description": "1-2 sentences: what business entity this table represents",
  "columns": {{
    "<COLUMN_NAME>": "10-30 words: business meaning of this column"
  }}
}}

Include ALL columns listed under the focus table. JSON:"""

        raw = await self.ai_provider.simple_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
        )
        data = self._parse_json(raw)

        if "description" in data and table.description_source != DescriptionSource.USER:
            table.enriched_description = data["description"].strip()
            table.description_source = DescriptionSource.AI

        cols_data: dict = data.get("columns", {})
        for col in table.columns:
            if col.description_source == DescriptionSource.USER:
                continue
            raw_desc = cols_data.get(col.name, "")
            if raw_desc:
                col.enriched_description = self._clean(str(raw_desc))
                col.description_source = DescriptionSource.AI

    # ------------------------------------------------------------------
    # Strategy 3: Legacy — original N+1 per-column calls (no cross-table ctx)
    # ------------------------------------------------------------------

    async def _enrich_table_legacy(self, schema_name: str, table: SchemaTable) -> None:
        table.enriched_description = await self._gen_table_description_legacy(
            schema_name, table
        )
        for col in table.columns:
            try:
                col.enriched_description = await self._gen_column_description_legacy(
                    table.name, col, table.sample_values
                )
            except Exception as exc:
                self.logger.error(
                    "Column description failed",
                    table=table.name,
                    column=col.name,
                    error=str(exc),
                )

    async def _gen_schema_description_legacy(self, schema: Schema) -> str:
        table_lines = []
        for t in schema.tables:
            rc = ""
            if t.sample_values and isinstance(t.sample_values, dict):
                count = t.sample_values.get("row_count")
                if count:
                    rc = f" ({count:,} rows)"
            table_lines.append(f"- {t.name}: {len(t.columns)} columns{rc}")

        prompt = (
            f"Analyze this database schema and provide a concise, business-focused description.\n\n"
            f"Database: {schema.name}\n"
            f"Type: {schema.db_type.value}\n"
            f"Tables ({len(schema.tables)}):\n"
            + "\n".join(table_lines)
            + "\n\nProvide a 1-2 sentence description explaining the primary purpose and domain. "
            "Be specific — no generic phrases like 'stores information'.\n\nDescription:"
        )

        result = await self.ai_provider.simple_completion(
            prompt=prompt, temperature=0.3, max_tokens=150
        )
        return result.strip()

    async def _gen_table_description_legacy(
        self, schema_name: str, table: SchemaTable
    ) -> str:
        col_lines = []
        for col in table.columns[:15]:
            flags = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_foreign_key:
                flags.append(f"FK->{col.foreign_key_table}")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            col_lines.append(f"- {col.name} ({col.data_type}){flag_str}")

        if len(table.columns) > 15:
            col_lines.append(f"... and {len(table.columns) - 15} more columns")

        prompt = (
            f"Analyze this database table and provide a clear, specific description.\n\n"
            f"Schema: {schema_name}\n"
            f"Table: {table.name}\n"
            f"Columns ({len(table.columns)}):\n"
            + "\n".join(col_lines)
            + "\n\nProvide a 1-2 sentence description explaining what business entity this table "
            "represents and its primary purpose. Use singular form.\n\nDescription:"
        )

        result = await self.ai_provider.simple_completion(
            prompt=prompt, temperature=0.3, max_tokens=100
        )
        return result.strip()

    async def _gen_column_description_legacy(
        self,
        table_name: str,
        column: SchemaColumn,
        sample_data: Optional[dict] = None,
    ) -> str:
        sample_text = ""
        if sample_data and isinstance(sample_data, dict):
            rows = sample_data.get("sample_rows", [])
            if rows and column.name in rows[0]:
                values = [str(r.get(column.name))[:50] for r in rows[:3]]
                sample_text = f"\nSample values: {', '.join(values)}"

        flags = []
        if column.is_primary_key:
            flags.append("Primary Key")
        if column.is_foreign_key:
            flags.append(
                f"Foreign Key to {column.foreign_key_table}.{column.foreign_key_column}"
            )
        if not column.is_nullable:
            flags.append("Required")

        flags_text = f"\nProperties: {', '.join(flags)}" if flags else ""

        prompt = (
            f"Describe this database column clearly and concisely.\n\n"
            f"Table: {table_name}\n"
            f"Column: {column.name}\n"
            f"Type: {column.data_type}{flags_text}{sample_text}\n\n"
            "Provide a SHORT (5-10 words) description explaining what this column stores. "
            "Focus on BUSINESS MEANING, not technical details. "
            "Don't repeat the column name or type.\n\nDescription:"
        )

        result = await self.ai_provider.simple_completion(
            prompt=prompt, temperature=0.3, max_tokens=50
        )
        return self._clean(result)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _render_full_schema(self, tables) -> str:
        """Compact but complete schema block for prompt inclusion."""
        parts = []
        for table in tables:
            parts.append(f"\nTABLE: {table.name}")

            if table.sample_values and isinstance(table.sample_values, dict):
                rc = table.sample_values.get("row_count")
                if rc:
                    parts.append(f"  ({rc:,} rows)")

            for col in table.columns:
                flags = []
                if col.is_primary_key:
                    flags.append("PK")
                if col.is_foreign_key:
                    flags.append(
                        f"FK→{col.foreign_key_table}.{col.foreign_key_column}"
                    )
                if not col.is_nullable:
                    flags.append("NOT NULL")
                if col.is_unique:
                    flags.append("UNIQUE")

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                parts.append(f"  {col.name} ({col.data_type}){flag_str}")

        return "\n".join(parts)

    def _render_relationships(self, tables) -> str:
        """Separate FK summary for cross-table relationship context."""
        lines = []
        for table in tables:
            for col in table.columns:
                if col.is_foreign_key and col.foreign_key_table:
                    lines.append(
                        f"  {table.name}.{col.name} → "
                        f"{col.foreign_key_table}.{col.foreign_key_column}"
                    )
        if not lines:
            return ""
        return "\n\nRELATIONSHIPS:\n" + "\n".join(lines)

    def _parse_json(self, raw: str) -> dict:
        """
        Extract and parse the JSON object from an AI response.
        Handles markdown code fences and extra surrounding text.
        """
        text = raw.strip()

        # Strip ```json ... ``` fences if present
        fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if fence:
            text = fence.group(1).strip()

        # Locate the outermost { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                f"No JSON object found in AI response (first 200 chars): {raw[:200]}"
            )

        return json.loads(text[start : end + 1])

    def _apply_data(self, schema: Schema, data: dict) -> None:
        """
        Apply a fully-parsed enrichment JSON dict to the Schema ORM objects.
        Skips any field whose description_source == 'user' (user-edited).
        """
        if "schema_description" in data and schema.description_source != DescriptionSource.USER:
            schema.enriched_description = str(data["schema_description"]).strip()
            schema.description_source = DescriptionSource.AI

        tables_data: dict = data.get("tables", {})

        for table in schema.tables:
            table_data = tables_data.get(table.name, {})

            if "description" in table_data and table.description_source != DescriptionSource.USER:
                table.enriched_description = str(table_data["description"]).strip()
                table.description_source = DescriptionSource.AI

            cols_data: dict = table_data.get("columns", {})
            for col in table.columns:
                if col.description_source == DescriptionSource.USER:
                    continue  # preserve user-edited column descriptions
                raw_desc = cols_data.get(col.name, "")
                if raw_desc:
                    col.enriched_description = self._clean(str(raw_desc))
                    col.description_source = DescriptionSource.AI

    @staticmethod
    def _clean(text: str) -> str:
        """Strip common AI verbosity prefixes and ensure capitalisation."""
        text = text.strip()
        for prefix in (
            "This column stores ",
            "This column contains ",
            "This column represents ",
            "Stores ",
            "Contains ",
            "Represents ",
            "The ",
            "A ",
        ):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        return text[0].upper() + text[1:] if text else text