"""Add study plan track

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-12

Добавляем фиксированный трек учебного плана, чтобы разделять Python и сети.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "study_plans",
        sa.Column(
            "track",
            sa.String(length=32),
            nullable=False,
            server_default="python",
        ),
    )
    op.create_index(op.f("ix_study_plans_track"), "study_plans", ["track"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_study_plans_track"), table_name="study_plans")
    op.drop_column("study_plans", "track")
