"""Add teams and user_team_members tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-07

Таблицы для командного домена:
- teams: группы сотрудников под руководством менеджера.
- user_team_members: связь many-to-many между пользователями и командами.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        # manager_id — SET NULL при удалении менеджера, команда остаётся без руководителя.
        sa.Column("manager_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_teams_manager_id"), "teams", ["manager_id"], unique=False)

    # Таблица связи many-to-many — без дополнительных атрибутов, только ключи.
    op.create_table(
        "user_team_members",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "team_id"),
    )


def downgrade() -> None:
    op.drop_table("user_team_members")
    op.drop_index(op.f("ix_teams_manager_id"), table_name="teams")
    op.drop_table("teams")
