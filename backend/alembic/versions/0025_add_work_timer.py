"""Add Work Timer module

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-12

Добавляем рабочий таймер с задачами, сессиями и журналом прерываний.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_timer_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_ref", sa.String(length=128), nullable=True),
        sa.Column("task_url", sa.String(length=2048), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="todo"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_timer_tasks_user_id", "work_timer_tasks", ["user_id"])
    op.create_index("ix_work_timer_tasks_status", "work_timer_tasks", ["status"])
    op.create_index("ix_work_timer_tasks_task_ref", "work_timer_tasks", ["task_ref"])
    op.create_index(
        "ix_work_timer_tasks_created_at", "work_timer_tasks", ["created_at"]
    )

    op.create_table(
        "work_timer_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("tags_snapshot", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["work_timer_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_work_timer_sessions_user_id", "work_timer_sessions", ["user_id"])
    op.create_index("ix_work_timer_sessions_task_id", "work_timer_sessions", ["task_id"])
    op.create_index("ix_work_timer_sessions_status", "work_timer_sessions", ["status"])
    op.create_index(
        "ix_work_timer_sessions_started_at", "work_timer_sessions", ["started_at"]
    )

    op.create_table(
        "work_timer_interruptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
            ["session_id"],
            ["work_timer_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_work_timer_interruptions_session_id",
        "work_timer_interruptions",
        ["session_id"],
    )
    op.create_index(
        "ix_work_timer_interruptions_started_at",
        "work_timer_interruptions",
        ["started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_work_timer_interruptions_started_at", table_name="work_timer_interruptions")
    op.drop_index("ix_work_timer_interruptions_session_id", table_name="work_timer_interruptions")
    op.drop_table("work_timer_interruptions")
    op.drop_index("ix_work_timer_sessions_started_at", table_name="work_timer_sessions")
    op.drop_index("ix_work_timer_sessions_status", table_name="work_timer_sessions")
    op.drop_index("ix_work_timer_sessions_task_id", table_name="work_timer_sessions")
    op.drop_index("ix_work_timer_sessions_user_id", table_name="work_timer_sessions")
    op.drop_table("work_timer_sessions")
    op.drop_index("ix_work_timer_tasks_created_at", table_name="work_timer_tasks")
    op.drop_index("ix_work_timer_tasks_task_ref", table_name="work_timer_tasks")
    op.drop_index("ix_work_timer_tasks_status", table_name="work_timer_tasks")
    op.drop_index("ix_work_timer_tasks_user_id", table_name="work_timer_tasks")
    op.drop_table("work_timer_tasks")

