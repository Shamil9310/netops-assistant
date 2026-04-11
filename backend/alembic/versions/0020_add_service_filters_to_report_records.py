"""Add service filters to report records

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-10 19:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "report_records",
        sa.Column(
            "service_filter_mode",
            sa.String(length=16),
            nullable=False,
            server_default="all",
        ),
    )
    op.add_column(
        "report_records",
        sa.Column("service_filters", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("report_records", "service_filters")
    op.drop_column("report_records", "service_filter_mode")
