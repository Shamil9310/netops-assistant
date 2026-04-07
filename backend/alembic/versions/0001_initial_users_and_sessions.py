"""Initial: users and user_sessions tables

Revision ID: 0001
Revises:
Create Date: 2026-04-07

Первая миграция — создаёт базовые таблицы для auth-слоя:
- users: хранит учётные записи сотрудников/менеджеров/разработчиков.
- user_sessions: хранит активные сессии (токены хранятся в виде хэша для безопасности).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Идентификатор этой миграции — используется Alembic для отслеживания версии БД.
revision: str = "0001"
# Предыдущая миграция — None означает начало цепочки.
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Применяет миграцию — создаёт таблицы users и user_sessions."""

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id"),
    )
    # Индекс на username — ускоряет поиск при логине (lookup по имени пользователя).
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        # Хэш токена хранится вместо самого токена — компрометация БД не даёт доступа к сессиям.
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # revoked_at — None означает активную сессию. Заполняется при logout.
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Индексы ускоряют поиск активных сессий по token_hash и user_id.
    op.create_index(op.f("ix_user_sessions_token_hash"), "user_sessions", ["token_hash"], unique=True)
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    """Откатывает миграцию — удаляет таблицы в обратном порядке.

    user_sessions удаляется первой, так как зависит от users по внешнему ключу.
    """
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_token_hash"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
