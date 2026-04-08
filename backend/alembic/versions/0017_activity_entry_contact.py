"""Add contact field to activity_entries

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("activity_entries", sa.Column("contact", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("activity_entries", "contact")
