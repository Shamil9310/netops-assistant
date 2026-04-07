"""Add planned_events table

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-07

Плановые события — будущие активности, запланированные заранее.
Включаются auto-include в дашборд текущего дня.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "planned_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        # scheduled_at — главное поле для фильтрации по дате.
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        # Ссылка на запись журнала при авто-включении — SET NULL при удалении записи.
        sa.Column("linked_journal_entry_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["linked_journal_entry_id"], ["activity_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planned_events_user_id"), "planned_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_planned_events_event_type"), "planned_events", ["event_type"], unique=False)
    # Индекс по scheduled_at критичен для запроса "события на сегодня".
    op.create_index(op.f("ix_planned_events_scheduled_at"), "planned_events", ["scheduled_at"], unique=False)
    op.create_index(op.f("ix_planned_events_external_ref"), "planned_events", ["external_ref"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_planned_events_external_ref"), table_name="planned_events")
    op.drop_index(op.f("ix_planned_events_scheduled_at"), table_name="planned_events")
    op.drop_index(op.f("ix_planned_events_event_type"), table_name="planned_events")
    op.drop_index(op.f("ix_planned_events_user_id"), table_name="planned_events")
    op.drop_table("planned_events")
