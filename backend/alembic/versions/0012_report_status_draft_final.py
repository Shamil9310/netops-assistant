"""Add report status draft/final

Revision ID: 0012
Revises: 0011
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "report_records",
        sa.Column("report_status", sa.String(length=32), nullable=False, server_default="draft"),
    )
    op.create_index(op.f("ix_report_records_report_status"), "report_records", ["report_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_report_records_report_status"), table_name="report_records")
    op.drop_column("report_records", "report_status")
