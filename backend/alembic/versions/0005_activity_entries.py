"""Add activity_entries table (journal domain)

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-07

Таблица журнала дневной операционной активности.
Центральная сущность day ops контура.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "activity_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_entries_user_id"), "activity_entries", ["user_id"], unique=False)
    op.create_index(op.f("ix_activity_entries_activity_type"), "activity_entries", ["activity_type"], unique=False)
    op.create_index(op.f("ix_activity_entries_status"), "activity_entries", ["status"], unique=False)
    op.create_index(op.f("ix_activity_entries_external_ref"), "activity_entries", ["external_ref"], unique=False)
    # Индекс по created_at критичен для запросов дашборда "за сегодня".
    op.create_index(op.f("ix_activity_entries_created_at"), "activity_entries", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_entries_created_at"), table_name="activity_entries")
    op.drop_index(op.f("ix_activity_entries_external_ref"), table_name="activity_entries")
    op.drop_index(op.f("ix_activity_entries_status"), table_name="activity_entries")
    op.drop_index(op.f("ix_activity_entries_activity_type"), table_name="activity_entries")
    op.drop_index(op.f("ix_activity_entries_user_id"), table_name="activity_entries")
    op.drop_table("activity_entries")
