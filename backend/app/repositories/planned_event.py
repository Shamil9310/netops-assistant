"""Репозиторий для работы с плановыми событиями."""

from __future__ import annotations

from datetime import date, datetime, timedelta, UTC
from uuid import UUID

from sqlalchemy import select

from app.models.planned_event import PlannedEvent
from app.repositories.base import BaseRepository


class PlannedEventRepository(BaseRepository[PlannedEvent]):
    """Репозиторий плановых событий пользователя."""

    async def list_for_user(
        self,
        user_id: UUID,
        include_completed: bool = False,
    ) -> list[PlannedEvent]:
        """Возвращает плановые события пользователя.

        По умолчанию возвращает только незавершённые события.
        Для архива передать include_completed=True.
        """
        query = (
            select(PlannedEvent)
            .where(PlannedEvent.user_id == user_id)
            .order_by(PlannedEvent.scheduled_at.asc())
        )
        if not include_completed:
            query = query.where(PlannedEvent.is_completed.is_(False))

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_for_today(self, user_id: UUID) -> list[PlannedEvent]:
        """Возвращает плановые события на сегодня (UTC)."""
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

        result = await self._session.execute(
            select(PlannedEvent)
            .where(PlannedEvent.user_id == user_id)
            .where(PlannedEvent.scheduled_at >= day_start)
            .where(PlannedEvent.scheduled_at <= day_end)
            .order_by(PlannedEvent.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_date(self, user_id: UUID, work_date: date) -> list[PlannedEvent]:
        """Возвращает плановые события на указанную рабочую дату."""
        day_start = datetime(
            work_date.year, work_date.month, work_date.day, 0, 0, 0, tzinfo=UTC
        )
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

        result = await self._session.execute(
            select(PlannedEvent)
            .where(PlannedEvent.user_id == user_id)
            .where(PlannedEvent.scheduled_at >= day_start)
            .where(PlannedEvent.scheduled_at <= day_end)
            .order_by(PlannedEvent.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, event_id: UUID, user_id: UUID) -> PlannedEvent | None:
        """Возвращает событие по ID, только если оно принадлежит пользователю.

        Двойная проверка защищает от IDOR — нельзя получить чужое событие по ID.
        """
        result = await self._session.execute(
            select(PlannedEvent)
            .where(PlannedEvent.id == event_id)
            .where(PlannedEvent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(self, event: PlannedEvent) -> PlannedEvent:
        """Сохраняет новое событие и возвращает его обновлённое состояние."""
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def update(self, event: PlannedEvent) -> PlannedEvent:
        """Коммитит изменения события."""
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def delete(self, event: PlannedEvent) -> None:
        """Удаляет плановое событие."""
        await self._session.delete(event)
        await self._session.commit()
