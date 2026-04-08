"""Add task_url to activity_entries

Revision ID: 0018
Revises: 0017
Create Date: 2026-04-08 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activity_entries",
        sa.Column("task_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("activity_entries", "task_url")
