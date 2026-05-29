"""add user role column and query_result share_expires_at

Revision ID: c5f8a2b4d1e3
Revises: b4e7f1a3c9d2
Create Date: 2026-05-28 00:02:00.000000

- users.role          : RBAC role string (viewer|editor|admin), default 'editor'
                        so all existing users retain their current access level.
- query_results.share_expires_at : optional DateTime for public share link expiry.
                        NULL = never expires (matches current behaviour for old rows).
"""
from alembic import op
import sqlalchemy as sa

revision      = "c5f8a2b4d1e3"
down_revision = "b4e7f1a3c9d2"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # Add role to users — nullable first so existing rows don't violate NOT NULL,
    # then backfill, then set server_default + NOT NULL.
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=True),
    )
    op.execute("UPDATE users SET role = 'editor' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False, server_default="editor")

    # Add optional share expiry to query_results
    op.add_column(
        "query_results",
        sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("query_results", "share_expires_at")
    op.drop_column("users", "role")
