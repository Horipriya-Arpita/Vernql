"""add_raw_ddl_text_to_schemas

Revision ID: b3d1e8f92c04
Revises: f4922e9c45fb
Create Date: 2026-04-20 00:00:00.000000

Stores the original uploaded schema text verbatim so it is never lost after
parsing. Also tracks the source format (sql_ddl, prisma, etc.) to enable
format-specific re-parsing and future Prisma support.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3d1e8f92c04'
down_revision = 'f4922e9c45fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # raw_ddl_text: verbatim text of whatever the user uploaded or pasted.
    # Nullable so existing rows are unaffected; new uploads always populate it.
    op.add_column(
        'schemas',
        sa.Column('raw_ddl_text', sa.Text(), nullable=True)
    )

    # schema_format: identifies how raw_ddl_text should be interpreted.
    # Current values: 'sql_ddl' | 'prisma'  (more formats added as parsers land)
    op.add_column(
        'schemas',
        sa.Column('schema_format', sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('schemas', 'schema_format')
    op.drop_column('schemas', 'raw_ddl_text')