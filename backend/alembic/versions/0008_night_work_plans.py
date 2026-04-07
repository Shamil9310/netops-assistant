"""Add night work plans, blocks, steps tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-07

Домен ночных работ:
- night_work_plans: план на одну ночь (контейнер изменений).
- night_work_blocks: блок внутри плана — один SR или одно изменение.
- night_work_steps: атомарный шаг внутри блока (команда, проверка, rollback).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "night_work_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_night_work_plans_user_id"), "night_work_plans", ["user_id"], unique=False)
    op.create_index(op.f("ix_night_work_plans_status"), "night_work_plans", ["status"], unique=False)
    op.create_index(op.f("ix_night_work_plans_created_at"), "night_work_plans", ["created_at"], unique=False)

    op.create_table(
        "night_work_blocks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("sr_number", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["night_work_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_night_work_blocks_plan_id"), "night_work_blocks", ["plan_id"], unique=False)
    op.create_index(op.f("ix_night_work_blocks_sr_number"), "night_work_blocks", ["sr_number"], unique=False)

    op.create_table(
        "night_work_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("block_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_rollback", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_post_action", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("actual_result", sa.Text(), nullable=True),
        sa.Column("executor_comment", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["block_id"], ["night_work_blocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_night_work_steps_block_id"), "night_work_steps", ["block_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_night_work_steps_block_id"), table_name="night_work_steps")
    op.drop_table("night_work_steps")
    op.drop_index(op.f("ix_night_work_blocks_sr_number"), table_name="night_work_blocks")
    op.drop_index(op.f("ix_night_work_blocks_plan_id"), table_name="night_work_blocks")
    op.drop_table("night_work_blocks")
    op.drop_index(op.f("ix_night_work_plans_created_at"), table_name="night_work_plans")
    op.drop_index(op.f("ix_night_work_plans_status"), table_name="night_work_plans")
    op.drop_index(op.f("ix_night_work_plans_user_id"), table_name="night_work_plans")
    op.drop_table("night_work_plans")
