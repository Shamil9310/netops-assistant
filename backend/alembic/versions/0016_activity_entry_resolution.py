"""Add resolution field to activity_entries

Revision ID: 0016
Revises: 0015
Create Date: 2026-04-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("activity_entries", sa.Column("resolution", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("activity_entries", "resolution")
