"""
Prisma Schema Parser
Parses .prisma schema syntax into the common SchemaInfo format.

Supports:
- model blocks with field definitions
- @id, @unique, @relation, @default, @updatedAt decorators
- Nullable fields (Type?)
- List/relation fields (Type[]) — skipped, they are not DB columns
- Enum types — mapped to VARCHAR(50)
- datasource block — extracts database provider automatically
- @@id([...]) composite primary keys
- @db.VarChar(n), @db.Text, etc. native type overrides
"""
import re
from typing import Dict, List, Optional, Set, Tuple
import structlog

from app.services.schema_parser import ColumnInfo, SchemaInfo, TableInfo

logger = structlog.get_logger()


# Prisma scalar type → PostgreSQL SQL type
_PG_TYPE_MAP: Dict[str, str] = {
    "String": "TEXT",
    "Int": "INTEGER",
    "BigInt": "BIGINT",
    "Float": "DOUBLE PRECISION",
    "Decimal": "DECIMAL",
    "Boolean": "BOOLEAN",
    "DateTime": "TIMESTAMP",
    "Json": "JSONB",
    "Bytes": "BYTEA",
}

# Prisma scalar type → MySQL SQL type
_MYSQL_TYPE_MAP: Dict[str, str] = {
    "String": "TEXT",
    "Int": "INT",
    "BigInt": "BIGINT",
    "Float": "DOUBLE",
    "Decimal": "DECIMAL",
    "Boolean": "TINYINT(1)",
    "DateTime": "DATETIME",
    "Json": "JSON",
    "Bytes": "BLOB",
}

# Prisma scalar types (everything else is a relation/enum)
_PRISMA_SCALARS: Set[str] = set(_PG_TYPE_MAP.keys())


class PrismaParser:
    """
    Parse Prisma schema files (.prisma) to extract schema structure.

    The parser does two passes over each model body:
    1. Collect @relation(fields: [...], references: [...]) to build an FK map.
    2. Parse each field line into a ColumnInfo, skipping relation objects and
       list fields that have no corresponding DB column.
    """

    def __init__(
        self,
        prisma_schema: str,
        db_type_override: Optional[str] = None,
    ) -> None:
        self.schema = prisma_schema
        self.db_type_override = db_type_override
        self.logger = logger.bind(parser="PrismaParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self) -> SchemaInfo:
        self.logger.info("Parsing Prisma schema", length=len(self.schema))

        db_type = self._detect_db_type()
        enum_names = self._collect_enum_names()
        model_names = self._collect_model_names()
        type_map = _MYSQL_TYPE_MAP if db_type == "mysql" else _PG_TYPE_MAP

        tables: List[TableInfo] = []
        for model_name, body in self._extract_model_blocks():
            columns = self._parse_model(model_name, body, model_names, enum_names, type_map)
            tables.append(
                TableInfo(
                    name=model_name,
                    columns=columns,
                    row_count=None,
                    comment=None,
                    sample_data=None,
                )
            )

        self.logger.info(
            "Prisma schema parsed",
            tables=len(tables),
            db_type=db_type,
        )

        return SchemaInfo(
            database_name="uploaded_schema",
            database_type=db_type,
            tables=tables,
            version=None,
        )

    # ------------------------------------------------------------------
    # Block extraction (brace-counting, robust against @default({...}))
    # ------------------------------------------------------------------

    def _extract_model_blocks(self) -> List[Tuple[str, str]]:
        """Return [(model_name, block_body), ...] for every model block."""
        results: List[Tuple[str, str]] = []
        text = self.schema
        pos = 0

        while pos < len(text):
            m = re.search(r'\bmodel\s+(\w+)\s*\{', text[pos:])
            if not m:
                break

            model_name = m.group(1)
            # Start depth counting from the character after the opening {
            body_start = pos + m.end()
            depth = 1
            j = body_start

            while j < len(text) and depth > 0:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1

            body = text[body_start : j - 1]
            results.append((model_name, body))
            # Advance past the opening brace of this model so the next search
            # starts inside the body (any nested models would be found too, but
            # Prisma doesn't allow nested models so this is safe).
            pos = pos + m.end()

        return results

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------

    def _detect_db_type(self) -> str:
        if self.db_type_override:
            return self.db_type_override.lower()

        m = re.search(
            r'datasource\s+\w+\s*\{[^}]*provider\s*=\s*["\'](\w+)["\']',
            self.schema,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            provider = m.group(1).lower()
            if provider in ("postgresql", "postgres"):
                return "postgresql"
            if provider == "mysql":
                return "mysql"

        return "postgresql"  # safe default

    def _collect_enum_names(self) -> Set[str]:
        return set(re.findall(r'\benum\s+(\w+)\s*\{', self.schema))

    def _collect_model_names(self) -> Set[str]:
        return set(re.findall(r'\bmodel\s+(\w+)\s*\{', self.schema))

    # ------------------------------------------------------------------
    # Model parsing
    # ------------------------------------------------------------------

    def _parse_model(
        self,
        model_name: str,
        body: str,
        model_names: Set[str],
        enum_names: Set[str],
        type_map: Dict[str, str],
    ) -> List[ColumnInfo]:
        # Pass 1: build FK map from @relation(fields:[...], references:[...])
        fk_map = self._build_fk_map(body, model_names)

        # Pass 2: build composite PK list from @@id([...])
        composite_pks = self._collect_composite_pks(body)

        # Pass 3: parse field lines into ColumnInfo
        columns: List[ColumnInfo] = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("@@"):
                continue

            col = self._parse_field_line(
                stripped,
                model_names,
                enum_names,
                type_map,
                fk_map,
                composite_pks,
            )
            if col is not None:
                columns.append(col)

        return columns

    def _build_fk_map(
        self, body: str, model_names: Set[str]
    ) -> Dict[str, Tuple[str, str]]:
        """
        Scan relation fields to map scalar FK column names → (ref_model, ref_field).

        Example Prisma line:
          user  User  @relation(fields: [userId], references: [id], onDelete: Cascade)
        → fk_map["userId"] = ("User", "id")
        """
        fk_map: Dict[str, Tuple[str, str]] = {}

        for line in body.splitlines():
            stripped = line.strip()
            rel_m = re.search(
                r'@relation\s*\([^)]*fields:\s*\[([^\]]+)\][^)]*references:\s*\[([^\]]+)\]',
                stripped,
            )
            if not rel_m:
                continue

            # Extract the type name from the beginning of the field line
            type_m = re.match(r'\w+\s+(\w+)', stripped)
            if not type_m:
                continue

            ref_model = type_m.group(1).rstrip("?")
            if ref_model not in model_names:
                continue

            fk_cols = [c.strip() for c in rel_m.group(1).split(",")]
            ref_cols = [c.strip() for c in rel_m.group(2).split(",")]

            for fk_col, ref_col in zip(fk_cols, ref_cols):
                fk_map[fk_col] = (ref_model, ref_col)

        return fk_map

    def _collect_composite_pks(self, body: str) -> List[str]:
        """Extract field names listed in @@id([...])."""
        for line in body.splitlines():
            m = re.match(r'\s*@@id\s*\(\[([^\]]+)\]\)', line)
            if m:
                return [c.strip() for c in m.group(1).split(",")]
        return []

    # ------------------------------------------------------------------
    # Field line parser
    # ------------------------------------------------------------------

    def _parse_field_line(
        self,
        line: str,
        model_names: Set[str],
        enum_names: Set[str],
        type_map: Dict[str, str],
        fk_map: Dict[str, Tuple[str, str]],
        composite_pks: List[str],
    ) -> Optional[ColumnInfo]:
        """
        Parse a single Prisma field line.
        Returns None for lines that don't represent a DB column:
          - relation object fields  (type is another model name)
          - list/array fields       (Type[])
        """
        # fieldName  FieldType[?[]]  rest...
        m = re.match(r'^(\w+)\s+(\w+)(\??)(\[\])?(.*)', line)
        if not m:
            return None

        field_name = m.group(1)
        field_type = m.group(2)
        is_optional = m.group(3) == "?"
        is_list = m.group(4) == "[]"
        rest = m.group(5).strip()

        # Skip list fields — they are relation arrays, not DB columns
        if is_list:
            return None

        # Skip relation object fields — type is another model and line has @relation
        if field_type in model_names:
            return None

        # Determine SQL data type
        if field_type in enum_names:
            sql_type = "VARCHAR(50)"
        elif field_type in type_map:
            sql_type = type_map[field_type]
        else:
            # Unknown scalar — fall back to TEXT
            sql_type = "TEXT"

        # Override with @db.NativeType if present  e.g. @db.VarChar(255) @db.Text
        native_m = re.search(r'@db\.(\w+)(?:\(([^)]*)\))?', rest)
        if native_m:
            native_name = native_m.group(1).upper()
            native_args = native_m.group(2)
            sql_type = f"{native_name}({native_args})" if native_args else native_name

        is_primary_key = "@id" in rest or field_name in composite_pks
        is_unique = "@unique" in rest and not is_primary_key
        # Required unless marked optional, but PKs are always NOT NULL
        is_nullable = is_optional and not is_primary_key

        # FK resolution from the fk_map built in pass 1
        is_foreign_key = field_name in fk_map
        foreign_key_table: Optional[str] = None
        foreign_key_column: Optional[str] = None
        if is_foreign_key:
            foreign_key_table, foreign_key_column = fk_map[field_name]

        return ColumnInfo(
            name=field_name,
            data_type=sql_type,
            is_nullable=is_nullable,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            foreign_key_table=foreign_key_table,
            foreign_key_column=foreign_key_column,
            default_value=None,
            is_unique=is_unique,
            is_auto_increment=False,
            comment=None,
        )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def parse_prisma_schema(
    prisma_schema: str,
    db_type_override: Optional[str] = None,
) -> SchemaInfo:
    """
    Parse a Prisma schema file into a SchemaInfo object.

    Args:
        prisma_schema: Raw text content of a .prisma file.
        db_type_override: Force a specific db_type instead of reading the
                          datasource block (useful when the block is absent).

    Returns:
        SchemaInfo with tables and columns derived from the Prisma models.
    """
    return PrismaParser(prisma_schema, db_type_override).parse()