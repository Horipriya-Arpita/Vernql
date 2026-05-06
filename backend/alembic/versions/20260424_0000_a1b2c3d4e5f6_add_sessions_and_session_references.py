"""add sessions table and session_id references to queries and query_results

Revision ID: a1b2c3d4e5f6
Revises: c7a2b9f1d4e8
Create Date: 2026-04-24 00:00:00.000000

Creates the sessions table for grouping queries into conversations and
adds nullable session_id FKs to queries and query_results. All new columns
are nullable so existing rows are unaffected (zero downtime migration).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c7a2b9f1d4e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schema_id', UUID(as_uuid=True), sa.ForeignKey('schemas.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(80), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_sessions_company_created', 'sessions', ['company_id', 'created_at'])
    op.create_index('ix_sessions_company_active', 'sessions', ['company_id', 'is_active'])

    # 2. Add session_id and turn_number to queries (both nullable — backward compatible)
    op.add_column(
        'queries',
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True)
    )
    op.add_column(
        'queries',
        sa.Column('turn_number', sa.Integer(), nullable=True)
    )
    op.create_index('ix_queries_session_turn', 'queries', ['session_id', 'turn_number'])

    # 3. Add session_id to query_results (nullable — backward compatible)
    op.add_column(
        'query_results',
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True)
    )
    op.create_index('ix_query_results_session_created', 'query_results', ['session_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_query_results_session_created', table_name='query_results')
    op.drop_column('query_results', 'session_id')

    op.drop_index('ix_queries_session_turn', table_name='queries')
    op.drop_column('queries', 'turn_number')
    op.drop_column('queries', 'session_id')

    op.drop_index('ix_sessions_company_active', table_name='sessions')
    op.drop_index('ix_sessions_company_created', table_name='sessions')
    op.drop_table('sessions')