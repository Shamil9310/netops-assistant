"""Add study progress fields

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-12

Добавляем хранение процентов усвоения темы и привязку сессии к конкретной теме.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "study_checkpoints",
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "study_sessions",
        sa.Column("checkpoint_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "study_sessions",
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        op.f("fk_study_sessions_checkpoint_id_study_checkpoints"),
        "study_sessions",
        "study_checkpoints",
        ["checkpoint_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_study_sessions_checkpoint_id"),
        "study_sessions",
        ["checkpoint_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_study_sessions_checkpoint_id"), table_name="study_sessions")
    op.drop_constraint(
        op.f("fk_study_sessions_checkpoint_id_study_checkpoints"),
        "study_sessions",
        type_="foreignkey",
    )
    op.drop_column("study_sessions", "progress_percent")
    op.drop_column("study_sessions", "checkpoint_id")
    op.drop_column("study_checkpoints", "progress_percent")
