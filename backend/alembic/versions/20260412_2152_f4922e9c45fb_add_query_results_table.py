"""add_query_results_table

Revision ID: f4922e9c45fb
Revises: a5b521f03b99
Create Date: 2026-04-12 21:52:02.024748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4922e9c45fb'
down_revision = 'a5b521f03b99'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'query_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('query_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('results_data', sa.JSON(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('column_count', sa.Integer(), nullable=False),
        sa.Column('chart_type', sa.String(), nullable=True),
        sa.Column('ai_insight', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['query_id'], ['queries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE')
    )

    # Add indexes for performance
    op.create_index('ix_query_results_query_id', 'query_results', ['query_id'])
    op.create_index('ix_query_results_company_id', 'query_results', ['company_id'])
    op.create_index('ix_query_results_created_at', 'query_results', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_query_results_created_at')
    op.drop_index('ix_query_results_company_id')
    op.drop_index('ix_query_results_query_id')
    op.drop_table('query_results')
