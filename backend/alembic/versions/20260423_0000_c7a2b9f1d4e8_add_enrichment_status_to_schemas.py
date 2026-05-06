"""add enrichment_status and enrichment_error to schemas

Revision ID: c7a2b9f1d4e8
Revises: e1c3d9f84b12
Create Date: 2026-04-23 00:00:00.000000

Adds enrichment_status (pending|running|complete|failed) and enrichment_error
to the schemas table so background enrichment failures are visible to users
instead of silently leaving the schema stuck in the "enriching..." state.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c7a2b9f1d4e8'
down_revision = 'e1c3d9f84b12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'schemas',
        sa.Column(
            'enrichment_status',
            sa.String(20),
            nullable=False,
            server_default='pending',
        ),
    )
    op.add_column(
        'schemas',
        sa.Column('enrichment_error', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('schemas', 'enrichment_error')
    op.drop_column('schemas', 'enrichment_status')