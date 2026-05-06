"""add description_source to schemas, schema_tables, schema_columns

Revision ID: d4f7b2e91a3c
Revises: b3d1e8f92c04
Create Date: 2026-04-20 00:01:00.000000

Tracks whether an enriched_description was written by AI ('ai') or
manually edited by the user ('user'). NULL means not yet enriched.
The enrichment service skips overwriting user-edited descriptions.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4f7b2e91a3c'
down_revision = 'b3d1e8f92c04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'schemas',
        sa.Column('description_source', sa.String(10), nullable=True),
    )
    op.add_column(
        'schema_tables',
        sa.Column('description_source', sa.String(10), nullable=True),
    )
    op.add_column(
        'schema_columns',
        sa.Column('description_source', sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('schema_columns', 'description_source')
    op.drop_column('schema_tables', 'description_source')
    op.drop_column('schemas', 'description_source')