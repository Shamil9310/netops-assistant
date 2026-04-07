"""Add work_date and ticket_number to activity entries

Revision ID: 0011
Revises: 0010
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("activity_entries", sa.Column("work_date", sa.Date(), nullable=True))
    op.add_column("activity_entries", sa.Column("ticket_number", sa.String(length=128), nullable=True))

    # Переносим рабочую дату из created_at для уже существующих записей.
    op.execute("UPDATE activity_entries SET work_date = (created_at AT TIME ZONE 'UTC')::date WHERE work_date IS NULL")
    # Сохраняем совместимость: ticket_number и external_ref синхронизируем для исторических строк.
    op.execute("UPDATE activity_entries SET ticket_number = external_ref WHERE ticket_number IS NULL")

    op.alter_column("activity_entries", "work_date", nullable=False)
    op.create_index(op.f("ix_activity_entries_work_date"), "activity_entries", ["work_date"], unique=False)
    op.create_index(op.f("ix_activity_entries_ticket_number"), "activity_entries", ["ticket_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_entries_ticket_number"), table_name="activity_entries")
    op.drop_index(op.f("ix_activity_entries_work_date"), table_name="activity_entries")
    op.drop_column("activity_entries", "ticket_number")
    op.drop_column("activity_entries", "work_date")
