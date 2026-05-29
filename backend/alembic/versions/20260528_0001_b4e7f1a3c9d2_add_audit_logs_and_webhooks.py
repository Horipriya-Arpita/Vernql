"""add audit_logs and webhooks tables

Revision ID: b4e7f1a3c9d2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-28 00:01:00.000000

Adds two new tables required for Q2 features:
- audit_logs : immutable compliance trail of every significant action
- webhooks   : registered server-to-server event delivery endpoints
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision    = "b4e7f1a3c9d2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # audit_logs                                                           #
    # ------------------------------------------------------------------ #
    op.create_table(
        "audit_logs",
        sa.Column("id",            UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("company_id",    UUID(as_uuid=True), nullable=False),
        sa.Column("user_id",       UUID(as_uuid=True), nullable=True),
        sa.Column("api_key_id",    UUID(as_uuid=True), nullable=True),
        sa.Column("action",        sa.String(60),       nullable=False),
        sa.Column("resource_type", sa.String(50),       nullable=True),
        sa.Column("resource_id",   UUID(as_uuid=True), nullable=True),
        sa.Column("details",       JSONB,               nullable=True),
        sa.Column("ip_address",    sa.String(45),       nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_logs_company_id",      "audit_logs", ["company_id"])
    op.create_index("ix_audit_logs_action",          "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at",      "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_company_created", "audit_logs", ["company_id", "created_at"])
    op.create_index("ix_audit_logs_company_action",  "audit_logs", ["company_id", "action"])

    # ------------------------------------------------------------------ #
    # webhooks                                                             #
    # ------------------------------------------------------------------ #
    op.create_table(
        "webhooks",
        sa.Column("id",                UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("company_id",        UUID(as_uuid=True), nullable=False),
        sa.Column("url",               sa.String(2048),    nullable=False),
        sa.Column("events",            JSONB,               nullable=False),
        sa.Column("signing_secret",    sa.String(128),     nullable=True),
        sa.Column("is_active",         sa.Boolean,         nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_code",  sa.Integer,         nullable=True),
    )
    op.create_index("ix_webhooks_company_id",     "webhooks", ["company_id"])
    op.create_index("ix_webhooks_is_active",      "webhooks", ["is_active"])
    op.create_index("ix_webhooks_company_active", "webhooks", ["company_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_webhooks_company_active", table_name="webhooks")
    op.drop_index("ix_webhooks_is_active",      table_name="webhooks")
    op.drop_index("ix_webhooks_company_id",     table_name="webhooks")
    op.drop_table("webhooks")

    op.drop_index("ix_audit_logs_company_action",  table_name="audit_logs")
    op.drop_index("ix_audit_logs_company_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at",      table_name="audit_logs")
    op.drop_index("ix_audit_logs_action",          table_name="audit_logs")
    op.drop_index("ix_audit_logs_company_id",      table_name="audit_logs")
    op.drop_table("audit_logs")
