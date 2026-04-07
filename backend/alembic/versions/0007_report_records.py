"""Add report_records table

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-07

История сгенерированных отчётов — daily, weekly, range.
Позволяет повторно открыть и скачать ранее сформированный отчёт.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "report_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("period_from", sa.String(length=10), nullable=False),
        sa.Column("period_to", sa.String(length=10), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_report_records_user_id"), "report_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_report_records_report_type"), "report_records", ["report_type"], unique=False)
    op.create_index(op.f("ix_report_records_created_at"), "report_records", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_records_created_at"), table_name="report_records")
    op.drop_index(op.f("ix_report_records_report_type"), table_name="report_records")
    op.drop_index(op.f("ix_report_records_user_id"), table_name="report_records")
    op.drop_table("report_records")
