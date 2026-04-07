"""Add handoff_to to night work steps

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("night_work_steps", sa.Column("handoff_to", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("night_work_steps", "handoff_to")
