"""Add auth_audit_events table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-07

Таблица аудита auth-событий: фиксирует входы, выходы и ошибки аутентификации.
Нужна для анализа безопасности и обнаружения брутфорса.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "auth_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        # user_id = NULL при LOGIN_FAILED — пользователь мог не существовать.
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("username_attempted", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("client_ip", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auth_audit_events_user_id"), "auth_audit_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_auth_audit_events_event_type"), "auth_audit_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_auth_audit_events_created_at"), "auth_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auth_audit_events_created_at"), table_name="auth_audit_events")
    op.drop_index(op.f("ix_auth_audit_events_event_type"), table_name="auth_audit_events")
    op.drop_index(op.f("ix_auth_audit_events_user_id"), table_name="auth_audit_events")
    op.drop_table("auth_audit_events")
