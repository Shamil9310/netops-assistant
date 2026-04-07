"""Add role column to users

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-07

Добавляет поле role в таблицу users для реализации RBAC.
Дефолт 'employee' — все существующие пользователи получают минимальную роль.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
            # employee — наименьшие привилегии, безопасный дефолт для существующих записей.
            server_default="employee",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
