"""Add service to activity_entries

Revision ID: 0019
Revises: 0018
Create Date: 2026-04-10 16:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_entries",
        sa.Column("service", sa.String(length=256), nullable=True),
    )
    op.create_index(
        "ix_activity_entries_service",
        "activity_entries",
        ["service"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_entries_service", table_name="activity_entries")
    op.drop_column("activity_entries", "service")
