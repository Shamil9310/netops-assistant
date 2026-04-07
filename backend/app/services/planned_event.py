from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import ActivityEntry, ActivityStatus, ActivityType
from app.models.planned_event import PlannedEvent, PlannedEventType

logger = logging.getLogger(__name__)


async def list_events(
    session: AsyncSession,
    user_id: UUID,
    include_completed: bool = False,
) -> list[PlannedEvent]:
    """Возвращает плановые события пользователя.

    По умолчанию возвращает только незавершённые события.
    Для архива передать include_completed=True.
    """
    query = select(PlannedEvent).where(PlannedEvent.user_id == user_id)

    if not include_completed:
        query = query.where(PlannedEvent.is_completed.is_(False))

    # Сортируем по времени начала — ближайшие события первыми.
    query = query.order_by(PlannedEvent.scheduled_at.asc())

    result = await session.execute(query)
    return list(result.scalars().all())


async def list_events_for_today(session: AsyncSession, user_id: UUID) -> list[PlannedEvent]:
    """Возвращает плановые события на сегодня (UTC).

    Используется для auto-include в дашборд текущего дня:
    события, запланированные на сегодня, автоматически попадают в дневной обзор.
    """
    now = datetime.now(UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

    result = await session.execute(
        select(PlannedEvent)
        .where(PlannedEvent.user_id == user_id)
        .where(PlannedEvent.scheduled_at >= day_start)
        .where(PlannedEvent.scheduled_at <= day_end)
        .order_by(PlannedEvent.scheduled_at.asc())
    )
    return list(result.scalars().all())


async def list_events_for_date(session: AsyncSession, user_id: UUID, work_date: date) -> list[PlannedEvent]:
    """Возвращает плановые события на указанную рабочую дату."""
    day_start = datetime(work_date.year, work_date.month, work_date.day, 0, 0, 0, tzinfo=UTC)
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

    result = await session.execute(
        select(PlannedEvent)
        .where(PlannedEvent.user_id == user_id)
        .where(PlannedEvent.scheduled_at >= day_start)
        .where(PlannedEvent.scheduled_at <= day_end)
        .order_by(PlannedEvent.scheduled_at.asc())
    )
    return list(result.scalars().all())


async def get_event_by_id(session: AsyncSession, event_id: UUID, user_id: UUID) -> PlannedEvent | None:
    """Возвращает событие по ID, только если оно принадлежит пользователю.

    Двойная проверка защищает от IDOR — нельзя получить чужое событие по ID.
    """
    result = await session.execute(
        select(PlannedEvent)
        .where(PlannedEvent.id == event_id)
        .where(PlannedEvent.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_event(
    session: AsyncSession,
    user_id: UUID,
    event_type: PlannedEventType,
    title: str,
    description: str | None,
    external_ref: str | None,
    scheduled_at: datetime,
) -> PlannedEvent:
    """Создаёт новое плановое событие."""
    event = PlannedEvent(
        user_id=user_id,
        event_type=event_type.value,
        title=title,
        description=description,
        external_ref=external_ref,
        scheduled_at=scheduled_at,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    logger.info("Создано плановое событие: id=%s, user_id=%s, type=%s", event.id, user_id, event_type)
    return event


async def update_event(
    session: AsyncSession,
    event: PlannedEvent,
    event_type: PlannedEventType | None,
    title: str | None,
    description: str | None,
    external_ref: str | None,
    scheduled_at: datetime | None,
    is_completed: bool | None,
    linked_journal_entry_id: UUID | None,
) -> PlannedEvent:
    """Обновляет плановое событие. None-значения не изменяются."""
    if event_type is not None:
        event.event_type = event_type.value
    if title is not None:
        event.title = title
    if description is not None:
        event.description = description
    if external_ref is not None:
        event.external_ref = external_ref
    if scheduled_at is not None:
        event.scheduled_at = scheduled_at
    if is_completed is not None:
        event.is_completed = is_completed
    if linked_journal_entry_id is not None:
        event.linked_journal_entry_id = linked_journal_entry_id

    await session.commit()
    await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event: PlannedEvent) -> None:
    """Удаляет плановое событие."""
    await session.delete(event)
    await session.commit()
    logger.info("Удалено плановое событие: id=%s", event.id)


async def convert_event_to_activity_entry(session: AsyncSession, event: PlannedEvent) -> ActivityEntry:
    """Конвертирует planned event в запись журнала и связывает сущности.

    Бизнес-смысл:
    заранее запланированная активность после фактического выполнения
    становится полноценной записью журнала для отчётности.
    """
    if event.linked_journal_entry_id is not None:
        existing_entry = await session.get(ActivityEntry, event.linked_journal_entry_id)
        if existing_entry is not None:
            return existing_entry

    journal_entry = ActivityEntry(
        user_id=event.user_id,
        work_date=event.scheduled_at.date(),
        activity_type=ActivityType.TASK.value,
        status=ActivityStatus.CLOSED.value if event.is_completed else ActivityStatus.OPEN.value,
        title=event.title,
        description=event.description,
        external_ref=event.external_ref,
        ticket_number=event.external_ref,
        started_at=event.scheduled_at,
        finished_at=event.scheduled_at if event.is_completed else None,
    )
    session.add(journal_entry)
    await session.flush()

    event.linked_journal_entry_id = journal_entry.id
    await session.commit()
    await session.refresh(journal_entry)
    await session.refresh(event)
    return journal_entry
