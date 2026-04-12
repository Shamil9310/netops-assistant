"""Add study modules

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-12

Добавляем сущность StudyModule — блок (раздел) учебного плана, который
группирует темы (checkpoints). Модуль позволяет разбить большой роадмап
на логические разделы и отслеживать прогресс по каждому из них отдельно.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_modules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["study_plans.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_study_modules_plan_id", "study_modules", ["plan_id"])

    op.add_column(
        "study_checkpoints",
        sa.Column("module_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_study_checkpoints_module_id",
        "study_checkpoints",
        "study_modules",
        ["module_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_study_checkpoints_module_id", "study_checkpoints", ["module_id"])


def downgrade() -> None:
    op.drop_index("ix_study_checkpoints_module_id", table_name="study_checkpoints")
    op.drop_constraint("fk_study_checkpoints_module_id", "study_checkpoints", type_="foreignkey")
    op.drop_column("study_checkpoints", "module_id")
    op.drop_index("ix_study_modules_plan_id", table_name="study_modules")
    op.drop_table("study_modules")
