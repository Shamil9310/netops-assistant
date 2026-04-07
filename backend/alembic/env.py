from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import Connection

from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401


alembic_cfg = context.config

if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запускает миграции в offline-режиме без реального подключения к БД."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(sync_connection: Connection) -> None:
    """Выполняет миграции через синхронное соединение внутри транзакции.

    Alembic ожидает именно синхронное соединение. Поэтому в async-сценарии
    мы передаём ему sync_connection через connection.run_sync(...).

    Самый важный момент здесь — явный context.begin_transaction().
    Без него Alembic может показать в логах выполнение миграций, но изменения
    не будут зафиксированы в базе данных.
    """
    context.configure(
        connection=sync_connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запускает миграции в online-режиме с реальным подключением к БД."""
    connectable = create_async_engine(settings.database_url, echo=False)

    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
