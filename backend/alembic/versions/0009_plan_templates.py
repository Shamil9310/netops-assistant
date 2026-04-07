"""Add plan templates table

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "plan_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "key", name="uq_plan_templates_user_id_key"),
    )
    op.create_index(op.f("ix_plan_templates_user_id"), "plan_templates", ["user_id"], unique=False)
    op.create_index(op.f("ix_plan_templates_category"), "plan_templates", ["category"], unique=False)
    op.create_index(op.f("ix_plan_templates_is_active"), "plan_templates", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plan_templates_is_active"), table_name="plan_templates")
    op.drop_index(op.f("ix_plan_templates_category"), table_name="plan_templates")
    op.drop_index(op.f("ix_plan_templates_user_id"), table_name="plan_templates")
    op.drop_table("plan_templates")
