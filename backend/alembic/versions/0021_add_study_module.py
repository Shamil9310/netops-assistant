"""Add study module tables

Revision ID: 0021
Revises: 0020
Create Date: 2026-04-11

Домены учёбы:
- study_plans: корневой учебный план.
- study_checkpoints: этапы и промежуточные точки.
- study_checklist_items: ручной чеклист внутри плана.
- study_sessions: таймерные сессии учёбы с паузами и остановками.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="draft"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_study_plans_user_id"), "study_plans", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_study_plans_status"), "study_plans", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_study_plans_created_at"), "study_plans", ["created_at"], unique=False
    )

    op.create_table(
        "study_checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_study_checkpoints_plan_id"),
        "study_checkpoints",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_checkpoints_is_done"),
        "study_checkpoints",
        ["is_done"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_checkpoints_completed_at"),
        "study_checkpoints",
        ["completed_at"],
        unique=False,
    )

    op.create_table(
        "study_checklist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"], ["study_checkpoints.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_study_checklist_items_plan_id"),
        "study_checklist_items",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_checklist_items_checkpoint_id"),
        "study_checklist_items",
        ["checkpoint_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_checklist_items_is_done"),
        "study_checklist_items",
        ["is_done"],
        unique=False,
    )

    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default="running"
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_study_sessions_plan_id"), "study_sessions", ["plan_id"], unique=False
    )
    op.create_index(
        op.f("ix_study_sessions_status"), "study_sessions", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_study_sessions_started_at"),
        "study_sessions",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_study_sessions_ended_at"), "study_sessions", ["ended_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_study_sessions_ended_at"), table_name="study_sessions")
    op.drop_index(op.f("ix_study_sessions_started_at"), table_name="study_sessions")
    op.drop_index(op.f("ix_study_sessions_status"), table_name="study_sessions")
    op.drop_index(op.f("ix_study_sessions_plan_id"), table_name="study_sessions")
    op.drop_table("study_sessions")

    op.drop_index(
        op.f("ix_study_checklist_items_is_done"), table_name="study_checklist_items"
    )
    op.drop_index(
        op.f("ix_study_checklist_items_checkpoint_id"),
        table_name="study_checklist_items",
    )
    op.drop_index(
        op.f("ix_study_checklist_items_plan_id"), table_name="study_checklist_items"
    )
    op.drop_table("study_checklist_items")

    op.drop_index(
        op.f("ix_study_checkpoints_completed_at"), table_name="study_checkpoints"
    )
    op.drop_index(op.f("ix_study_checkpoints_is_done"), table_name="study_checkpoints")
    op.drop_index(op.f("ix_study_checkpoints_plan_id"), table_name="study_checkpoints")
    op.drop_table("study_checkpoints")

    op.drop_index(op.f("ix_study_plans_created_at"), table_name="study_plans")
    op.drop_index(op.f("ix_study_plans_status"), table_name="study_plans")
    op.drop_index(op.f("ix_study_plans_user_id"), table_name="study_plans")
    op.drop_table("study_plans")
