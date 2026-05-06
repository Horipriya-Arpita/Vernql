"""add is_unique to schema_columns

Revision ID: e1c3d9f84b12
Revises: d4f7b2e91a3c
Create Date: 2026-04-22 00:00:00.000000

Adds is_unique boolean to schema_columns so the enrichment service can
include UNIQUE constraint flags in the schema context sent to the LLM.
Without this column, enrichment_service._render_full_schema() raises
AttributeError on every call.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1c3d9f84b12'
down_revision = 'd4f7b2e91a3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'schema_columns',
        sa.Column('is_unique', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('schema_columns', 'is_unique')