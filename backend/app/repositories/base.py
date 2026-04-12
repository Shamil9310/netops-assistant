"""Базовый класс репозитория.

Содержит общие методы работы с сессией SQLAlchemy.
Конкретные репозитории наследуются от BaseRepository и добавляют
методы, специфичные для своей сущности.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Базовый репозиторий с общими операциями над сессией.

    Параметр ModelT — ORM-модель, с которой работает репозиторий.
    Используется только для типизации, конкретные запросы определяются
    в наследниках.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий с сессией базы данных."""
        self._session = session

    async def flush(self) -> None:
        """Сбрасывает pending-изменения в БД без коммита транзакции."""
        await self._session.flush()

    async def commit(self) -> None:
        """Коммитит текущую транзакцию."""
        await self._session.commit()

    async def refresh(self, instance: ModelT) -> None:
        """Обновляет объект из базы данных после записи."""
        await self._session.refresh(instance)

    def add(self, instance: ModelT) -> None:
        """Добавляет объект в сессию (без немедленной записи в БД)."""
        self._session.add(instance)

    def add_all(self, instances: list[ModelT]) -> None:
        """Добавляет список объектов в сессию."""
        self._session.add_all(instances)

    async def delete(self, instance: ModelT) -> None:
        """Удаляет объект из БД и коммитит изменение."""
        await self._session.delete(instance)
        await self._session.commit()
