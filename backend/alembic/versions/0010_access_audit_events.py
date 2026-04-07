"""Add access audit events table

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "access_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("target_user_id", sa.Uuid(), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_audit_events_user_id"), "access_audit_events", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_access_audit_events_target_user_id"),
        "access_audit_events",
        ["target_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_audit_events_resource_type"),
        "access_audit_events",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_audit_events_resource_id"),
        "access_audit_events",
        ["resource_id"],
        unique=False,
    )
    op.create_index(op.f("ix_access_audit_events_action"), "access_audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_access_audit_events_created_at"), "access_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_access_audit_events_created_at"), table_name="access_audit_events")
    op.drop_index(op.f("ix_access_audit_events_action"), table_name="access_audit_events")
    op.drop_index(op.f("ix_access_audit_events_resource_id"), table_name="access_audit_events")
    op.drop_index(op.f("ix_access_audit_events_resource_type"), table_name="access_audit_events")
    op.drop_index(op.f("ix_access_audit_events_target_user_id"), table_name="access_audit_events")
    op.drop_index(op.f("ix_access_audit_events_user_id"), table_name="access_audit_events")
    op.drop_table("access_audit_events")
