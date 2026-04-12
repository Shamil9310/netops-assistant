"""Репозиторий для работы с записями журнала активности.

Содержит все SQL-запросы к таблице ActivityEntry.
Сервисный слой не должен содержать прямых вызовов SQLAlchemy —
только методы этого репозитория.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import or_, select

from app.models.journal import ActivityEntry
from app.repositories.base import BaseRepository


class JournalRepository(BaseRepository[ActivityEntry]):
    """Репозиторий записей журнала активности."""

    async def list_for_date(
        self,
        user_id: str | UUID,
        work_date: date,
    ) -> list[ActivityEntry]:
        """Возвращает записи пользователя за конкретную рабочую дату.

        Сортировка: сначала по started_at (nulls last), затем по created_at.
        Это обеспечивает предсказуемый порядок даже если время не указано.
        """
        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.work_date == work_date)
            .order_by(
                ActivityEntry.started_at.asc().nullslast(),
                ActivityEntry.created_at.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        user_id: str | UUID,
        entry_id: str | UUID,
    ) -> ActivityEntry | None:
        """Возвращает запись по ID в рамках пользователя-владельца.

        Явная фильтрация по user_id гарантирует, что пользователь
        не получит чужую запись даже при подборе ID.
        """
        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.id == str(entry_id))
        )
        return result.scalar_one_or_none()

    async def list_for_date_range(
        self,
        user_id: str | UUID,
        date_from: date,
        date_to: date,
    ) -> list[ActivityEntry]:
        """Возвращает записи пользователя за диапазон дат.

        Фильтрация идёт по work_date, а не по created_at:
        запись, внесённая позже, всё равно попадает в отчёт
        за исходную рабочую дату.
        """
        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.work_date >= date_from)
            .where(ActivityEntry.work_date <= date_to)
            .order_by(
                ActivityEntry.work_date.asc(),
                ActivityEntry.started_at.asc().nullslast(),
                ActivityEntry.created_at.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_last_finished_time_for_date(
        self,
        user_id: str | UUID,
        work_date: date,
    ) -> datetime | None:
        """Возвращает время завершения последней записи за рабочую дату.

        Используется для автоподстановки started_at в новой записи:
        следующая запись часто начинается сразу после предыдущей.
        """
        result = await self._session.execute(
            select(ActivityEntry.finished_at)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.work_date == work_date)
            .where(ActivityEntry.finished_at.is_not(None))
            .order_by(
                ActivityEntry.finished_at.desc(),
                ActivityEntry.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save(self, entry: ActivityEntry) -> ActivityEntry:
        """Сохраняет новую запись и возвращает её обновлённое состояние из БД."""
        self._session.add(entry)
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def save_all(self, entries: list[ActivityEntry]) -> list[ActivityEntry]:
        """Сохраняет список новых записей и возвращает их обновлённое состояние."""
        self._session.add_all(entries)
        await self._session.commit()
        for entry in entries:
            await self._session.refresh(entry)
        return entries

    async def update(self, entry: ActivityEntry) -> ActivityEntry:
        """Коммитит изменения записи и возвращает её обновлённое состояние."""
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def delete(self, entry: ActivityEntry) -> None:
        """Удаляет запись журнала."""
        await self._session.delete(entry)
        await self._session.commit()

    async def delete_for_date(
        self,
        user_id: str | UUID,
        work_date: date,
    ) -> int:
        """Удаляет все записи пользователя за выбранную рабочую дату.

        Возвращает количество удалённых записей.
        """
        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.work_date == work_date)
        )
        entries = list(result.scalars().all())
        if not entries:
            return 0

        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()
        return len(entries)

    async def delete_all(self, user_id: str | UUID) -> int:
        """Удаляет все записи журнала пользователя.

        Явная фильтрация по user_id гарантирует, что операция
        никогда не затрагивает чужой журнал.
        """
        result = await self._session.execute(
            select(ActivityEntry).where(ActivityEntry.user_id == str(user_id))
        )
        entries = list(result.scalars().all())
        if not entries:
            return 0

        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()
        return len(entries)

    async def delete_selected(
        self,
        user_id: str | UUID,
        entry_ids: list[str],
    ) -> int:
        """Удаляет выбранные записи пользователя.

        Безопасность: фильтрация по user_id гарантирует,
        что чужие ID не дадут доступ к чужим записям.
        """
        normalized_ids = [eid.strip() for eid in entry_ids if eid.strip()]
        if not normalized_ids:
            return 0

        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.id.in_(normalized_ids))
        )
        entries = list(result.scalars().all())
        if not entries:
            return 0

        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()
        return len(entries)

    async def list_with_ticket_for_date(
        self,
        user_id: str | UUID,
        work_date: date,
    ) -> list[ActivityEntry]:
        """Возвращает записи за дату у которых задан ticket_number.

        Используется для поиска дублей при дедупликации.
        Сортировка: ticket_number → created_at → id — для детерминированного выбора
        «первой» записи при удалении дублей.
        """
        result = await self._session.execute(
            select(ActivityEntry)
            .where(ActivityEntry.user_id == str(user_id))
            .where(ActivityEntry.work_date == work_date)
            .where(ActivityEntry.ticket_number.is_not(None))
            .order_by(
                ActivityEntry.ticket_number.asc(),
                ActivityEntry.created_at.asc(),
                ActivityEntry.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_existing_ticket_pairs(
        self,
        user_id: str | UUID,
        ticket_date_pairs: set[tuple[str, date]],
    ) -> set[tuple[str, date]]:
        """Возвращает уже существующие пары ticket_number + work_date.

        Используется при Excel-импорте для защиты от создания дублей:
        мы проверяем какие из импортируемых пар уже есть в БД
        и пропускаем их.
        """
        if not ticket_date_pairs:
            return set()

        filters = [
            (ActivityEntry.ticket_number == ticket_number)
            & (ActivityEntry.work_date == work_date)
            for ticket_number, work_date in ticket_date_pairs
        ]
        result = await self._session.execute(
            select(ActivityEntry.ticket_number, ActivityEntry.work_date)
            .where(ActivityEntry.user_id == str(user_id))
            .where(or_(*filters))
        )
        return {
            (ticket_number, work_date)
            for ticket_number, work_date in result.all()
            if ticket_number is not None
        }
